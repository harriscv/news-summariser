# -*- coding: UTF-8 -*-
# cd C:\Users\krwh821\OneDrive - AZCollaboration\Python Scripts\NewsSummary\data\processed
# Harris Vince
# Start date: 15/04/2019
import os
import time
import requests
import numpy as np
import datetime

# import nltk

# from nltk.corpus import wordnet as wn
# from nltk.corpus import sentiwordnet as swn
from gensim.summarization import summarize
from bs4 import BeautifulSoup
from fpdf import FPDF


class StoryLinks:
    """
    Searches SKY news homepage and gets the links to all stories.
    """

    def __init__(self, homepage):
        self.homepage = homepage

    def get_story_links(self):
        # Extract HTML from page
        request = requests.get(self.homepage)
        all_html = request.text
        soup = BeautifulSoup(all_html, features="lxml")

        # Use relevant attributes to collect first n examples
        all_a = soup.find_all("a")
        top_stories = []
        for string in all_a:
            hrefs = string.get("href")
            if hrefs[:7] == "/story/":
                top_stories.append(self.homepage + hrefs)

        return top_stories


class GetArticleFromSoup:
    """
    Scrape soup on a page and get body and title.
    """

    def __init__(self, top_stories):
        self.top_stories = top_stories

    def get_soup(self, article_num):
        all_html = requests.get(self.top_stories[article_num]).text
        soup = BeautifulSoup(all_html, features="lxml")
        return soup

    def get_body_and_title(self, article_num):
        soup = self.get_soup(article_num)

        # get body
        all_p = soup.find_all("p", class_=False)
        all_body = []
        for string in all_p:
            all_body.append(string.get_text())

        # get title
        titles = soup.find_all("title")
        article_title = titles[0].get_text()

        # get article relevant info
        article = [all_body, article_title]
        return article


class AnalyseArticle:
    """
    For soup from one page, this class will return a range of parameters related to the article.
    """

    def __init__(self, article):
        self.body = article[0]
        self.title = article[1]

    def clean_title(self):
        """remove unneccesary info from title"""
        remove_tags = self.title[: self.title.index("|")]
        return str(remove_tags.encode("ascii", "ignore").decode("ascii"))

    @staticmethod
    def chunk_body(seq):

        num = np.ceil(0.1 * len(seq))
        try:
            avg = len(seq) / float(num)
        except ZeroDivisionError:
            avg = len(seq)

        chunked_body = []
        last = 0.0
        while last < len(seq):
            chunked_body.append(seq[int(last) : int(last + avg)])
            last += avg

        return chunked_body

    def body_summary(self):
        chunked_body = self.chunk_body(self.body[1:])
        # TODO: if sentence has 'he', 'she', 'they', etc... then add the previous sentence
        body_text = []
        for chunk in chunked_body:
            try:
                # make chunk into single sentence
                text = " ".join(chunk)
                text.replace("\\", "")
                body_text.append(summarize(text))

            # if chunk is too short just put the whole thing in there
            except ValueError:
                body_text = chunk

        body_summarised = " ".join(body_text)

        # remove mess
        body_summarised = (
            body_summarised.replace("  ", " ")
            .replace(r"\u", "")
            .replace("::", "")
            .replace(r"\\", "")
            .replace("\u2026", "")
            .replace("\u2019", "")
            .replace("\u20ac", "")
            # .replace("\U0001f4f8", "'")
            # .replace("\U0001f64f", "")
            # .replace("\u200e", "")
        )
        body_summarised.encode("ascii", "ignore").decode("ascii")

        return body_summarised

    def get_summary_sentence(self):
        try:
            summary = self.body[0]
            return str(summary.encode("ascii", "ignore").decode("ascii"))
        except IndexError:
            return []

    @staticmethod
    def get_positivity_of_body():
        # breakdown = list(swn.senti_synset("hello"))
        # breakdown.pos_score()
        # breakdown.neg_score()
        # breakdown.obj_score()
        # return breakdown
        # TODO: positivity score
        pass

    def reading_time(self):
        """
        :return: estimate of time saved due to reading the summary instead of original website
        """
        num_words_bef = len(str(self.body).split())
        num_words_aft = len(str(self.body_summary()).split())

        # estimated reading params
        word_reading_freq = 3  # (per second) average per person
        time_spent_clicking_and_scrolling = 20  # seconds

        delta_words = num_words_bef - num_words_aft
        time_reading_article = (
            delta_words / word_reading_freq + time_spent_clicking_and_scrolling
        )

        return time_reading_article

    def article_params(self):
        tl = self.clean_title()
        sm = self.get_summary_sentence()
        bd = self.body_summary()
        rt = self.reading_time()

        return tl, sm, bd, rt


class FormatReport:
    def __init__(self):
        self.pdf = FPDF()

    def intro(self):
        self.pdf.set_margins(10, 10, 10)
        self.pdf.add_page()
        self.pdf.set_font("Arial", "B", 16)
        self.pdf.cell(40, 10, "Summary of Today's News")
        self.pdf.ln()
        self.pdf.set_font("Arial", "B", 14)
        self.pdf.cell(40, 10, "SKY")

    def write_one(self, tl, sm, bd):
        self.pdf.ln()
        self.pdf.set_font("Arial", "B", 11)
        self.pdf.multi_cell(0, 5, tl)
        self.pdf.ln()
        self.pdf.set_font("Arial", "I", 10)
        self.pdf.multi_cell(0, 5, str(sm))
        self.pdf.ln()
        self.pdf.set_font("Arial", "", 10)
        self.pdf.multi_cell(0, 5, bd)

    def footer(self, comp_time, read_time):
        self.pdf.ln()
        self.pdf.set_font("Arial", "", 10)
        self.pdf.cell(
            0,
            8,
            f"Autogenerated by Harris Vince on {datetime.datetime.now().date()} in {round(comp_time, 5)}s. "
            f"Reading this saved you {time.strftime('%M:%S', time.gmtime(int(read_time)))}min.",
            # f"(or {time.strftime('%M:%S', time.gmtime(saved_seconds_erin))} if you are Erin).",
            0,
            0,
            "C",
        )

    def save(self):
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath("scripts")))
        self.pdf.output(
            os.path.join(
                project_dir,
                "data",
                "processed",
                f"news_summary_{datetime.datetime.now().date()}.pdf",
            ),
            "F",
        )


# Get article links
links = StoryLinks("https://news.sky.com/").get_story_links()

titles, summary_sentences, bodies, reading_times = [], [], [], []
for report_num in range(len(links)):
    article_info = GetArticleFromSoup(links).get_body_and_title(report_num)
    title, summary_sentence, body, reading_time = AnalyseArticle(
        article_info
    ).article_params()
    titles.append(title)
    summary_sentences.append(summary_sentence)
    bodies.append(body)
    reading_times.append(reading_time)

# Remove duplicate articles (sometimes the same article will be in multiple links)
seen = set()
unique_titles = []
for title in titles:
    if title not in seen:
        seen.add(title)
        unique_titles.append(title)
indices_of_uniques = np.asarray(
    sorted([titles.index(x) for x in list(set(titles).intersection(unique_titles))])
)

# Keep only values with indices of unique values
all_articles_sum = []
for ind in indices_of_uniques:
    all_articles_sum.append(
        [titles[ind], summary_sentences[ind], bodies[ind], reading_times[ind]]
    )

# --------------
# TOP 10 STORIES:
# --------------
report = FormatReport()
report.intro()
start = time.time()
tot_read_time = []
for ttl, sms, bod, rtt in all_articles_sum[:15]:
    if len(bod) == 0:
        pass
    else:
        print(ttl)
        report.write_one(ttl, sms, bod)
        tot_read_time.append(rtt)
end = time.time()

# footer and save
report.footer(end - start, sum(tot_read_time))
report.save()

print(f"-- \nNews on {datetime.datetime.now()}")

# -----------------------
# TOP 10 POSITIVE STORIES:
# -----------------------
# TODO: determine which stories are positive / negative
# report = FormatReport()
# report.intro()
# start = time.time()
# tot_read_time = []
# for ttl, sms, bod, rtt in all_articles_sum[:10]:
#     try:
#         report.write_one(ttl, sms, bod)
#         tot_read_time.append(rtt)
#     except AttributeError:
#         pass
# end = time.time()
#
# # footer and save
# report.footer(end - start, sum(tot_read_time))
# report.save()

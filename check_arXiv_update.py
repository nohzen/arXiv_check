import os
import yaml
import requests
import datetime
import urlextract
import arxiv


def query_topic(topic, args, date_from):
    keywords = args["keywords"]
    categories = args["categories"]
    only_with_url = args["only_with_url"]

    # Category query
    query_cat = "("
    for i in range(len(categories)):
        cat = "cat:" + categories[i]
        query_cat += cat
        if i != len(categories) - 1:
            query_cat += " OR "
    query_cat += ")"

    # Keyword query
    query_keyword = "("
    for i in range(len(keywords)):
        keyword = 'all:"' + keywords[i] + '"'
        query_keyword += keyword
        if i != len(keywords) - 1:
            query_keyword += " OR "
    query_keyword += ")"

    now = datetime.datetime.now(datetime.timezone.utc)
    query_date = "lastUpdatedDate:[{:%Y%m%d%H%M%S} TO {:%Y%m%d%H%M%S}]".format(date_from, now)
    query = query_cat + " AND " + query_keyword + " AND " + query_date
    print(query)


    client = arxiv.Client()
    extractor = urlextract.URLExtract()

    search = arxiv.Search(
        query = query,
        max_results = 20,
        sort_by = arxiv.SortCriterion.LastUpdatedDate
        # LastUpdatedDate or SubmittedDate
    )

    file_path = "output.md"
    file = open(file_path, 'a')
    file.write("# " + topic + "\n")

    results = client.results(search)
    lastUpdateDate = date_from

    for result in results:
        print(result)
        # result.entry_id, result.title, result.published, result.updated, result.authors, result.summary, result.categories, result.comment

        urls = set()
        # Get URL from abst
        abstract = result.summary
        if abstract is not None:
            # ref: https://stackoverflow.com/questions/9760588/how-do-you-extract-a-url-from-a-string-using-python
            urls.update(set(extractor.find_urls(abstract)))
        # Get URL from comment
        comment = result.comment
        if comment is not None:
            urls.update(set(extractor.find_urls(comment)))
        # Get URL from paperwithcode
        paperwithcode_url = "https://arxiv.paperswithcode.com/api/v0/papers/"
        paper_id = result.get_short_id()
        code_url = paperwithcode_url + paper_id
        r = requests.get(code_url).json()
        if "official" in r and r["official"]:
            urls.add(r["official"]["url"])

        lastUpdateDate = lastUpdateDate if lastUpdateDate > result.updated else result.updated
        if only_with_url and len(urls) == 0:
            continue

        # Write
        file.write("## " + result.authors[0].name.split()[-1] + "+ ")
        file.write('"' + result.title + '" ')
        file.write('{:(%Y-%m-%d)}'.format(result.published) + "\n")
        file.write(result.entry_id + "\n")
        for url in urls:
            file.write(url + "\n")
        # file.write('{:(%Y-%m-%d %H:%M:%S)}'.format(result.published) + "\n")
        # file.write('{:(%Y-%m-%d %H:%M:%S)}'.format(result.updated) + "\n")
        file.write("\n")


    file.write("\n")
    file.close()
    return lastUpdateDate



def test():
    id = "2405.14870v1"
    search = arxiv.Search(id_list=[id])
    client = arxiv.Client()
    result = next(client.results(search))
    print(result.title)
    print(result.authors)
    print(result.summary)
    print(result.comment)


if __name__ == "__main__":
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)

    date_file = "lastUpdateDate.yaml"
    if os.path.isfile(date_file):
        with open(date_file, "r") as file:
            date_from = yaml.safe_load(file)
            date_from = date_from["lastUpdateDate"]
    else:
        print("There are no datetime file!:", date_file)
        date_from = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=4)

    lastUpdateDate = date_from
    for topic, args in config["topics"].items():
        print(topic)
        topicLastUpdateDate = query_topic(topic, args, date_from)
        lastUpdateDate = lastUpdateDate if lastUpdateDate > topicLastUpdateDate else topicLastUpdateDate
        print("\n")

    date = {"lastUpdateDate": lastUpdateDate}
    with open(date_file, "w") as file:
        yaml.dump(date, file)


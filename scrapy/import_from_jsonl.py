import argparse
import jsonlines
import os
import uuid

from scrapy_app.solr_call import solr_add, solr_add_file

parser = argparse.ArgumentParser(
    description='Example with nonoptional arguments',
)

parser.add_argument('solr', action="store",
                    help='Solr hostname (expects to find a documents and files core there). eg: http://solr:8983')
parser.add_argument('jsonl', action="store",
                    help='Location of the jsonlines file')

args = parser.parse_args()


print("Reading: " + args.jsonl)
count_docs = 0
count_files = 0
with jsonlines.open(args.jsonl) as reader:
    for item in reader:
        print("Processing document: " +
              item['title'] + ' (' + item['id'] + ')')
        solr_add(core="documents", docs=[item])
        count_docs += 1
        if 'pdf_docs' in item:
            for url in item['pdf_docs']:
                pdf_id = str(uuid.uuid5(uuid.NAMESPACE_URL, url))
                path = os.path.basename(url)
                file = open(os.environ['SCRAPY_FILES_FOLDER'] +
                            'files/' + item['website'] + "/" + path, mode='rb')
                print('Processing file: ' + str(file.name) + ' (' + pdf_id + ')')
                solr_add_file('files', file, pdf_id, url, item['id'])
                count_files += 1

print('Process ' + str(count_docs) +
      ' document and ' + str(count_files)+' files')

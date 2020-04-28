#!/bin/bash

COLLECTION="documents"
SOLR_HOST="https://solr.dev.dgfisma.crosslang.com"

JSON='{"add-field": [
{"name":"title",            "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"title_prefix",     "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"author",           "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"status",           "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"type",             "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"date",             "type":"pdates","stored":true,"indexed":true,"multiValued":true},
{"name":"url"               "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"ELI",              "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"celex",            "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"website",          "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"summary",          "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"various",          "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"content",          "type":"text_general","stored":true,"indexed":true,"multiValued":true}
{"name":"pull",             "type":"boolean","stored":true,"indexed":true,"multiValued":true}
]
}';

curl -k -X POST --user crosslang:***REMOVED*** -H 'Content-type:application/json' --data-binary "$JSON" $SOLR_HOST/solr/$COLLECTION/schema

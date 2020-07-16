#!/bin/bash

COLLECTION="documents"
#SOLR_HOST="https://solr.dev.dgfisma.crosslang.com"
SOLR_HOST="http://localhost:8983"


JSON='{"add-field": [
{"name":"title",            "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"title_prefix",     "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"author",           "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"status",           "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"type",             "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"date",             "type":"pdates","stored":true,"indexed":true,"multiValued":true},
{"name":"date_last_update", "type":"pdate","stored":true,"indexed":true,"multiValued":false},
{"name":"url"               "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"eli",              "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"celex",            "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"website",          "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"summary",          "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"various",          "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"content",          "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"content_html",     "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"pull",             "type":"boolean","stored":true,"indexed":true,"multiValued":true},
{"name":"pdf_docs",         "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"pages",            "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"reference",        "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"section",          "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"tags",             "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"keywords",         "type":"text_general","stored":true,"indexed":true,"multiValued":true},

{"name":"file",             "type":"text_general","stored":true,"indexed":true},
{"name":"file_url",         "type":"text_general","stored":true,"indexed":true},

{"name":"acceptance_state",         "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"accepted_probability",     "type":"pdoubles","stored":true,"indexed":true,"multiValued":true},

{"name":"amendments_act",           "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"amendments_comment",       "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"amendments_from",          "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"amendments_relation",      "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"amendments_subdivision",   "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"amendments_to",            "type":"text_general","stored":true,"indexed":true,"multiValued":true},

{"name":"classifications",          "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"classifications_code",     "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"classifications_label",    "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"classifications_type",     "type":"text_general","stored":true,"indexed":true,"multiValued":true},

{"name":"dates",                    "type":"pdates","stored":true,"indexed":true,"multiValued":true},
{"name":"dates_info",               "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"dates_type",               "type":"text_general","stored":true,"indexed":true,"multiValued":true},

{"name":"created_at",               "type":"pdates","stored":true,"indexed":true,"multiValued":true},
{"name":"updated_at",               "type":"pdates","stored":true,"indexed":true,"multiValued":true},

{"name":"misc",                            "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"misc_additional_information",     "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"misc_addressee",                  "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"misc_author",                     "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"misc_department_responsible",     "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"misc_form",                       "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"misc_internal_reference",         "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"misc_internal_comment",           "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"misc_parliamentary_term",         "type":"text_general","stored":true,"indexed":true,"multiValued":true},

{"name":"procedure",                       "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"procedure_co_author",             "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"procedures_links_name",           "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"procedures_links_url",            "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"procedures_number",               "type":"text_general","stored":true,"indexed":true,"multiValued":true},

{"name":"relationships",                   "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"relationships_legal_basis",       "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"relationships_oj_link",           "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"relationships_proposal",          "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"relationships_treaty",            "type":"text_general","stored":true,"indexed":true,"multiValued":true},

{"name":"consolidated_versions",           "type":"text_general","stored":true,"indexed":true,"multiValued":true},

{"name":"spider",          "type":"text_general","stored":true,"indexed":true,"multiValued":true},
{"name":"task",            "type":"text_general","stored":true,"indexed":true,"multiValued":true},
]
}';

curl -k -X POST --user crosslang:isthebest -H 'Content-type:application/json' --data-binary "$JSON" $SOLR_HOST/solr/$COLLECTION/schema
curl -k --user crosslang:isthebest $SOLR_HOST/solr/$COLLECTION/config -d '{"set-user-property": {"update.autoCreateFields":"false"}}'

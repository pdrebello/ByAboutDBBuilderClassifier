###Configurations required for By-Statement Extraction (do not change the order)
requiredCategs = ['FRONT_PAGE', 'REGIONAL_NEWS','NATIONAL_NEWS', 'INTERNATIONAL_NEWS', 'SPORTS', 'BUSINESS', 'OPINION']               

mongoConfigs = {
'host':'127.0.0.1',
'port':27017,
'db':'media-db'
}
esConfigs = {
'host':'10.237.26.25',
'port':9200,
'db':'media-db'
}

resolved_entity_table = 'entities_resolved_overall'
article_table = 'aadhar'
by_about_table = 'by_about'

proxy_server='https://act4d.iitd.ernet.in:3128'

entity_types = ["Organization","Company"]
short_sources_list = ["Hindu", "TOI", "HT", "IE", "DecH", "Telegraph", "NIE"]
sources_list = ["News18","NDTV","The Hindu", "The Times Of India", "Hindustan Times", "Indian Express", "Deccan Herald", "Telegraph", "The New Indian Express"]

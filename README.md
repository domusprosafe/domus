# domus
NEEDED CONFIGURATION:



# client/config_all/domus/appconfig.py
## each URL should be a real webservice

DB_SYNCH_URL_HSTORE = 'custom_webservice.url'

DB_MERGE_URL = 'custom_webservice.url'

CONNECTION_CHECK_URL = 'custom_webservice.url'

DIFFPATCH_URL = 'custom_webservice.url'

ESKY_FILES_DOWNLOAD_URL = 'custom_webservice.url'

CHECK_ACTIVATION_CODE_URL = 'custom_webservice.url'

CHECK_PETALS_URL = 'custom_webservice.url'

SERVER_QUERY_URL = 'custom_webservice.url'

SECONDARY_PASSWORD_URL = 'custom_webservice.url'




# client/mainlogic.py
## custom_encryption_key should really be custom encryption keys

publicEncryptionKey = 'custom_encryption_key'

masterFileEncryptionKey = 'custom_encryption_key'



# client/prosafemaster.py
## custom_encryption_key should really be custom encryption keys

publicEncryptionKey = 'custom_encryption_key'

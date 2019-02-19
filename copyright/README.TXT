To automatically update the copyright blurbs present in this project,
first install the copyright module: it is available in cpanel-lvemanager gerrit
repository, path protractor-tests/running_from_jenkins_jobs/check_copyright/copyright.py.

Then run the following commands from the governor repository root:
    copyright/add_copyright.sh OR copyright/update_copyright.sh (if copyright is already in place)
    copyright/substitute_authors_with_csv.py copyright/file_authors.csv
NOTE: for a newly created repository please use the following command
    copyright/extract_authors_to_csv.py > copyright/file_authors.csv
    (sometimes, it might be necessary to manually update/review these changes)

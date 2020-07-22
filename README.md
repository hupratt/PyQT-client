# Python desktop app

## Architecture

- The ui.py is the entry point for building the app into a .exe file and can be run as a standalone .py script
- The ui.py calls 3 standalone apps. 
- The scrape_aris.py app spins up a firefox session controlled by selenium and ouputs a .xlsx and raw unstructured data in the form of .xls files.
- The create_tcs.py script reads up the .xls files into panda dataframes and generates test cases in .xlsx, csv as well as on JIRA directly. The creation on JIRA is handled by the [atlassian-api library](https://github.com/atlassian-api/atlassian-python-api). Once created the test case ID is saved in the original .xlsx file created earlier. This .xlsx file can be considered as the defacto database of the app. There is no need to switch to a regular database because 1) it is not part of the requirements 2) as of today there is a small volume of data being processed and 3) the testing flexibility offered by using an excel file.
- The sync.py script reads in the .json created by the create_tcs script and the database to log any differences with the test cases living on the JIRA server
- The user interface is built thanks to the opensource [PyQT5 library](https://www.riverbankcomputing.com/software/pyqt/intro). This library serves as a python binding to the popular [qt framework](https://www.qt.io/) written in C++
- The user interface makes heavy use of [the pyqtconfig open source project](https://github.com/mfitzp/pyqtconfig)

## Features

* [x] Desktop App: [Jira](https://www.atlassian.com/fr/software/jira) interfacing with the [ARIS business process management (BPM) application](https://www.bpmleader.com/software-ag-aris-business-process-analysis-platform/)
* [x] Reporting: Standalone scripts that manipulate data from Jira's REST API and output excel reports

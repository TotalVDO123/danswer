<!-- DANSWER_METADATA={"link": "https://github.com/danswer-ai/danswer/blob/main/backend/danswer/connectors/README.md"} -->

# Writing a new Danswer Connector
This README covers how to contribute a new Connector for Danswer. It includes an overview of the design, interfaces,
and required changes.

Thank you for your contribution!

### Connector Overview
Connectors come in 3 different flows:
- Load Connector:
  - Bulk indexes documents to reflect a point in time. This type of connector generally works by either pulling all
  documents via a connector's API or loads the documents from some sort of a dump file.
- Poll connector:
  - Incrementally updates documents based on a provided time range. It is used by the background job to pull the latest
  changes additions and changes since the last round of polling. This connector helps keep the document index up to date
  without needing to fetch/embed/index every document which generally be too slow to do frequently on large sets of
  documents.
- Event Based connectors:
  - Connectors that listen to events and update documents accordingly.
  - Currently not used by the background job, this exists for future design purposes.


### Connector Implementation
Refer to [interfaces.py](https://github.com/danswer-ai/danswer/blob/main/backend/danswer/connectors/interfaces.py)
and this first contributor created Pull Request for a new connector (Shoutout to Dan Brown):
[Reference Pull Request](https://github.com/danswer-ai/danswer/pull/139)

#### Implementing the new Connector
The connector must subclass one or more of LoadConnector, PollConnector, or EventConnector.

The `__init__` should take arguments for configuring what documents the connector will and where it finds those
documents. For example, if you have a wiki site, it may include the configuration for the team, topic, folder, etc. of
the documents to fetch. It may also include the base domain of the wiki. Alternatively, if all the access information
of the connector is stored in the credential/token, then there may be no required arguments.

`load_credentials` should take a dictionary which provides all the access information that the connector might need.
For example this could be the user's username and access token.

Refer to the existing connectors for `load_from_state` and `poll_source` examples. There is not yet a process to listen
for EventConnector events, this will come down the line.

#### Development Tip
It may be handy to test your new connector separate from the rest of the stack while developing.
Follow the below template:

```commandline
if __name__ == "__main__":
    import time
    test_connector = NewConnector(space="engineering")
    test_connector.load_credentials({
        "user_id": "foobar",
        "access_token": "fake_token"
    })
    all_docs = test_connector.load_from_state()
    
    current = time.time()
    one_day_ago = current - 24 * 60 * 60  # 1 day
    latest_docs = test_connector.poll_source(one_day_ago, current)
```

> Note: Be sure to set PYTHONPATH to danswer/backend before running the above main.


### Additional Required Changes:
#### Backend Changes
- Add a new type to
[DocumentSource](https://github.com/danswer-ai/danswer/blob/main/backend/danswer/configs/constants.py)
- Add a mapping from DocumentSource (and optionally connector type) to the right connector class
[here](https://github.com/danswer-ai/danswer/blob/main/backend/danswer/connectors/factory.py#L33)

#### Frontend Changes
- Add the new Connector definition to the `SOURCE_METADATA_MAP` [here](https://github.com/danswer-ai/danswer/blob/main/web/src/lib/sources.ts#L59).
- Add the definition for the new Form to the `connectorConfigs` object [here](https://github.com/danswer-ai/danswer/blob/main/web/src/lib/connectors/connectors.ts#L79). 

#### Docs Changes
Create the new connector page (with guiding images!) with how to get the connector credentials and how to set up the
connector in Danswer. Then create a Pull Request in https://github.com/danswer-ai/danswer-docs.

### Before opening PR
1. Be sure to fully test changes end to end with setting up the connector and updating the index with new docs from the
new connector. To make it easier to review, please attach a video showing the successful creation of the connector via the UI (starting from the `Add Connector` page).
2. Add a folder + tests under `backend/tests/daily/connectors` director. For an example, checkout the [test for Confluence](https://github.com/danswer-ai/danswer/blob/main/backend/tests/daily/connectors/confluence/test_confluence_basic.py). In the PR description, include a guide on how to setup the new source to pass the test. Before merging, we will re-create the environment and make sure the test(s) pass.  
3. Be sure to run the linting/formatting, refer to the formatting and linting section in
[CONTRIBUTING.md](https://github.com/danswer-ai/danswer/blob/main/CONTRIBUTING.md#formatting-and-linting)
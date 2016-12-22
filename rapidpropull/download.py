import temba_client.v1

import rapidpropull.cache

__author__ = 'Tomasz J. Kotarba <tomasz@kotarba.net>'
__copyright__ = 'Copyright (c) 2016, Tomasz J. Kotarba. All rights reserved.'
__maintainer__ = 'Tomasz J. Kotarba'
__email__ = 'tomasz@kotarba.net'


class DownloadTask(object):
    """
    Provides a mechanism for querying RapidPro servers and pulling data from
    them.  The downloaded data can be represented as RapidPro objects (see:
    rapidpro-python) or serialised to JSON.
    """
    def __init__(self, processed_arguments):
        """Create a download task for the specified ArgumentProcessor."""
        self.client = temba_client.v1.TembaClient(
            processed_arguments.get_address(),
            processed_arguments.get_api_token())
        self.endpoint_selector = processed_arguments.get_endpoint_selector()
        self.endpoint_kwargs = processed_arguments.get_endpoint_kwargs()
        self.selectors_of_requested_associations =\
            processed_arguments.get_selectors_of_requested_associations()
        cache_url = processed_arguments.get_cache_url()
        if cache_url is None:
            self.cache = None
        else:
            self.cache = rapidpropull.cache.RapidProCache(cache_url)
        self._downloaded_data = None

    def download(self):
        """
        Execute the download task - i.e. download and store matching objects
        from RapidPro.

        Stores a list of objects or a dictionary of lists in case --with-flows
        or --with-contacts were used.

        Example for --with-flows --with-contacts:
            {'runs': [run1, run2, ...],
             'flows': [flow1, flow2, ...],
             'contacts': [contact2, contact2, ...]}

        Example for --with-contacts:
            {'runs': [run1, ...],
             'contacts': [contact1, ...]}

        Example for --with-flows:
            {'runs': [run1, ...],
             'flows': [flow1, ...]}
        """
        endpoint_data = self._get_endpoint()(**self.endpoint_kwargs)
        if self.cache:
            self.cache.substitute_cached_for_downloaded(endpoint_data)
        if not self.selectors_of_requested_associations:
            self._downloaded_data = endpoint_data
        else:
            self._download_associated_data(endpoint_data)
        if self.cache:
            self.cache.insert_objects(self._downloaded_data)

    def get_downloaded_objects(self):
        """
        If any object have been downloaded, return a list or a dictionary
        containing all downloaded objects as instances of classes Contact, Flow
        or Run (see: rapidpro-python).  Otherwise, return None.
        """
        return self._downloaded_data

    def get_downloaded_json_structure(self):
        """
        Return a JSON structure (not a text string) with all downloaded objects
        serialised.  E.g. [{'uuid': 'object1'}, {'uuid': 'object2'}, ...].
        """
        result = None
        if isinstance(self._downloaded_data, list):
            result = []
            for item in self._downloaded_data:
                result.append(item.serialize())
        elif isinstance(self._downloaded_data, dict):
            result = {}
            for k in self._downloaded_data:
                result[k] = [o.serialize() for o in self._downloaded_data[k]]
        return result

    def overwrite_downloaded_data(self, data):
        """Overwrite stored downloaded data with the value of argument data."""
        self._downloaded_data = data

    def _get_endpoint(self, endpoint_selector=None):
        if endpoint_selector is None:
            endpoint_selector = self.endpoint_selector
        if endpoint_selector == '--flow-runs':
            return self.client.get_runs
        elif endpoint_selector == '--flows':
            return self.client.get_flows
        elif endpoint_selector == '--contacts':
            return self.client.get_contacts
        else:
            raise ValueError('Invalid endpoint selector "{}"'.format(
                endpoint_selector))

    def _download_associated_data(self, flowruns):
        all_data = {'runs': flowruns}
        for endpoint_selector in self.selectors_of_requested_associations:
            container_attr = endpoint_selector.lstrip('-')
            uuid_attr = container_attr.rstrip('s')
            all_data[container_attr] = []
            uuids = set()
            for run in flowruns:
                uuids.add(getattr(run, uuid_attr))
            if self.cache:
                from_cache, missing_uuids = self.cache.get_objects(
                    endpoint_selector, uuids)
                uuids = missing_uuids
                all_data[container_attr].extend(from_cache)
            all_data[container_attr].extend(self._get_endpoint(
                endpoint_selector)(uuids=uuids))
        self._downloaded_data = all_data

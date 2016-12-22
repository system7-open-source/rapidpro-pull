import random
import uuid

import temba_client.v1.types
# noinspection PyPackageRequirements
import pytest
# noinspection PyPackageRequirements
import behave.model

import rapidpropull
import rapidpropull.cli
import rapidpropull.download


__author__ = 'Tomasz J. Kotarba <tomasz@kotarba.net>'
__copyright__ = 'Copyright (c) 2016, Tomasz J. Kotarba. All rights reserved.'
__maintainer__ = 'Tomasz J. Kotarba'
__email__ = 'tomasz@kotarba.net'


class Auxiliary(object):
    @staticmethod
    def make_download_task(endpoint_selector, expected_download,
                           temba_client_class, optional_argv=None):
        if endpoint_selector == '--flow-runs':
            temba_client_class.return_value.get_runs.return_value = \
                expected_download
        elif endpoint_selector == '--flows':
            temba_client_class.return_value.get_flows.return_value = \
                expected_download
        elif endpoint_selector == '--contacts':
            temba_client_class.return_value.get_contacts.return_value = \
                expected_download
        else:
            pytest.fail('Unknown endpoint selector "{}"'.format(
                endpoint_selector))
        argv = [
            endpoint_selector, '--api-token=token',
            '--after=1111-11-11T11:11:11.111110Z',
            '--before=1111-11-11T11:11:11.111111Z',
        ]
        if optional_argv:
            argv.extend(optional_argv)
        arguments = rapidpropull.cli.ArgumentProcessor(argv)
        return rapidpropull.download.DownloadTask(arguments)

    @staticmethod
    def _get_full_behave_table(table):
        result = behave.model.Table(headings=[u'object_type', u'object_id',
                                              u'attribute_names',
                                              u'attribute_values'])
        if not table.rows:
            return result
        flow_runs = set()
        flows = set()
        contacts = set()
        if table.headings == result.headings:
            return table
        elif set(table.headings) == {u'run', u'flow', u'contact'}:
            for row in table:
                flow_run = row['run']
                flow = row['flow']
                contact = row['contact']
                if flow:
                    if flow not in flows:
                        result.add_row([u'flow', flow, u'', u''])
                        flows.add(flow)
                if contact:
                    if contact not in contacts:
                        result.add_row([u'contact', contact, u'', u''])
                        contacts.add(contact)
                if flow_run:
                    if flow_run not in flow_runs:
                        attribute_names = []
                        attribute_values = []
                        if flow:
                            attribute_names.append(u'flow_uuid')
                            attribute_values.append(flow)
                        if contact:
                            attribute_names.append(u'contact')
                            attribute_values.append(contact)
                        result.add_row([u'flow run', flow_run,
                                        u','.join(attribute_names),
                                        u','.join(attribute_values)])
                        flow_runs.add(flow_run)
            return result
        else:
            raise ValueError('Invalid table:\n{}\n'.format(table.headings))

    @staticmethod
    def index_objects_by_id(dict_from_make_objects):
        return {
            'flow runs': {o.id: o for o in dict_from_make_objects['flow runs']},
            'flows': {o.uuid: o for o in dict_from_make_objects['flows']},
            'contacts': {o.uuid: o for o in dict_from_make_objects['contacts']}
        }

    @classmethod
    def make_objects(cls, table):
        """
        Make a dictionary of RapidPro objects specified in a given Behave table.
        The following two table formats are supported:

        Example 1 - simplified table:
            |run|flow   |contact|
            |1  |ff1    |cc1    |
            |   |ff2    |cc2    |
            |   |ff3    |       |
            |   |       |cc3    |

        Example 2 - full table:
            |object_type|object_id  |attribute_names|attribute_values   |
            |run        |1          |contact,flow   |cc1,ff1            |
            |run        |2          |               |                   |
            |flow       |ff2        |name,runs      |some name,4        |
        """
        result = {'flow runs': {}, 'flows': {}, 'contacts': {}}
        table = cls._get_full_behave_table(table)
        for row in table:
            rapidpro_object = cls.make_object(row['object_type'],
                                              row['object_id'],
                                              row['attribute_names'],
                                              row['attribute_values'])
            if isinstance(rapidpro_object, temba_client.v1.types.Run):
                assert rapidpro_object.id not in result['flow runs']
                result['flow runs'][rapidpro_object.id] = rapidpro_object
            elif isinstance(rapidpro_object, temba_client.v1.types.Flow):
                assert rapidpro_object.uuid not in result['flows']
                result['flows'][rapidpro_object.uuid] = rapidpro_object
            elif isinstance(rapidpro_object, temba_client.v1.types.Contact):
                assert rapidpro_object.uuid not in result['contacts']
                result['contacts'][rapidpro_object.uuid] = rapidpro_object
        for k in result:
            result[k] = result[k].values()
        return result

    @classmethod
    def make_object(cls, object_type, object_id,
                    attribute_names='', attribute_values=''):
        """
        Make a RapidPro object with specified ID and attribute values.
        Arguments attribute_names and attribute_values should be CSV strings.
        """
        attribute_names = [
            s.strip() for s in attribute_names.split(',') if s]
        attribute_values = [
            s.strip() for s in attribute_values.split(',') if s]
        attributes = dict(zip(attribute_names, attribute_values))
        if 'run' in object_type:
            return cls.make_flow_run(run=int(object_id), **attributes)
        elif object_type == 'flow':
            return cls.make_flow(uuid=object_id, **attributes)
        elif object_type == 'contact':
            return cls.make_contact(uuid=object_id, **attributes)
        else:
            raise ValueError('Unknown object type "{}"'.format(object_type))

    @staticmethod
    def make_flow_run(**kwargs):
        run_id = random.randint(0, 9999)
        run_json = {
            u'run': run_id,
            u'completed': False,
            u'expired_on': None,
            u'flow_uuid': u'flow{}'.format(run_id),
            u'created_on': None,
            u'contact': u'contact{}'.format(run_id),
            u'values': [],
            u'modified_on': None,
            u'steps': [],
            u'expires_on': None
        }
        run_json.update(kwargs)
        return temba_client.v1.types.Run.deserialize(run_json)

    @staticmethod
    def make_flow(**kwargs):
        flow_uuid = str(uuid.uuid1())
        flow_json = {
            u'uuid': flow_uuid,
            u'runs': 3,
            u'expires': None,
            u'name': u'flow {}'.format(flow_uuid),
            u'labels': [],
            u'rulesets': [],
            u'created_on': None,
            u'archived': True,
            u'completed_runs': 1
        }
        flow_json.update(kwargs)
        return temba_client.v1.types.Flow.deserialize(flow_json)

    @staticmethod
    def make_contact(**kwargs):
        contact_uuid = str(uuid.uuid1())
        contact_json = {
            u'uuid': contact_uuid,
            u'name': u'contact {}'.format(contact_uuid),
            u'language': None,
            u'fields': [],
            u'urns': [],
            u'failed': False,
            u'group_uuids': [],
            u'modified_on': None,
            u'blocked': False,
        }
        contact_json.update(kwargs)
        return temba_client.v1.types.Contact.deserialize(contact_json)

    @staticmethod
    def make_serializable(value):

        class Serializable(object):
            def __init__(self, data):
                self.data = data

            def serialize(self):
                return hash(self.data)

        return Serializable(value)

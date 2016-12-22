import json

import sqlalchemy
import sqlalchemy.types
import temba_client.v1.types

__author__ = 'Tomasz J. Kotarba <tomasz@kotarba.net>'
__copyright__ = 'Copyright (c) 2016, Tomasz J. Kotarba. All rights reserved.'
__maintainer__ = 'Tomasz J. Kotarba'
__email__ = 'tomasz@kotarba.net'


class RapidProCache(object):
    """
    Provides a specialised caching mechanism for RapidPro objects (see:
    rapidpro-python).  Works with any local or remote relational database
    supported by SQLAlchemy - e.g. PostgreSQL, Oracle, SQLite.
    """
    INVALID_TYPE = 'Invalid type "{}".  The object must be an instance of' \
                   ' Run, Flow or Contact.'
    INVALID_ENDPOINT_SELECTOR = 'Invalid endpoint selector "{}".'

    def __init__(self, cache_url):
        """
        Initialise a RapidPro cache object and prepare it to interact with a
        database specified with cache_url.
        """
        self.database = self._initialise_database(cache_url)
        self._flowruns = self.database.tables['flowrun']
        self._flows = self.database.tables['flow']
        self._contacts = self.database.tables['contact']

    def insert_objects(self, objects):
        """
        Insert RapidPro objects (given as a list or a dictionary of lists) into
        the database.  The list elements must be instances of Contact, Flow or
        Run (see: rapidpro-python).
        """
        if not isinstance(objects, dict):
            objects = {'objects': objects}
        for k in objects:
            for o in objects[k]:
                self._insert_object(o)

    def get_objects(self, endpoint_selector, uuids):
        """
        Return a tuple consisting of 0) a list of cached objects matching UUIDs
        and 1) a set of UUIDs for all of the requested objects not in cache.
        Raise exception if unknown endpoint selector supplied.
        """
        pk_name = 'uuid'
        if endpoint_selector == '--flow-runs':
            deserialiser = temba_client.v1.types.Run.deserialize
            table_name = 'flowrun'
            pk_name = 'run'
        elif endpoint_selector == '--flows':
            deserialiser = temba_client.v1.types.Flow.deserialize
            table_name = 'flow'
        elif endpoint_selector == '--contacts':
            deserialiser = temba_client.v1.types.Contact.deserialize
            table_name = 'contact'
        else:
            raise ValueError(self.INVALID_ENDPOINT_SELECTOR.format(
                endpoint_selector))
        table = self.database.tables[table_name]
        records = self.database.bind.execute(
            table.select().where(table.c[pk_name].in_(uuids))).fetchall()
        cached_uuids = {getattr(r, pk_name) for r in records}
        cached = [deserialiser(json.loads(r.json)) for r in records]
        return cached, uuids.difference(cached_uuids)

    def substitute_cached_for_downloaded(self, objects):
        """
        *IN PLACE* For each object given in a list 'objects' of RapidPro objects
        (see: rapidpro-python), check if an object with the same ID is already
        stored in cache and, if this is the case, replace the object in the list
        with its cached counterpart.
        """
        for i in range(len(objects)):
            o = objects[i]
            if isinstance(o, temba_client.v1.types.Run):
                cached = self.get_flow_run(o.id)
            elif isinstance(o, temba_client.v1.types.Flow):
                cached = self.get_flow(o.uuid)
            elif isinstance(o, temba_client.v1.types.Contact):
                cached = self.get_contact(o.uuid)
            else:
                raise TypeError(self.INVALID_TYPE.format(type(o)))
            if cached:
                objects[i] = cached

    def get_flow_run(self, run_id):
        """
        Return an instance of Run (see: rapidpro-python) from cache if a flow
        run identified with run_id found in cache.
        """
        select = self._flowruns.select().where(self._flowruns.c.run == run_id)
        fr = self.database.bind.execute(select).fetchone()
        if fr is not None:
            return temba_client.v1.types.Run.deserialize(json.loads(fr.json))
        else:
            return None

    def get_flow(self, flow_uuid):
        """
        Return an instance of Flow (see: rapidpro-python) from cache if a flow
        identified with flow_uuid found in cache.
        """
        select = self._flows.select().where(self._flows.c.uuid == flow_uuid)
        flow = self.database.bind.execute(select).fetchone()
        if flow is not None:
            return temba_client.v1.types.Flow.deserialize(json.loads(flow.json))
        else:
            return None

    def get_contact(self, contact_uuid):
        """
        Return an instance of Contact (see: rapidpro-python) from cache if a
        contact identified with contact_uuid found in cache.
        """
        select = self._contacts.select().where(
            self._contacts.c.uuid == contact_uuid)
        contact = self.database.bind.execute(select).fetchone()
        if contact is not None:
            return temba_client.v1.types.Contact.deserialize(
                json.loads(contact.json))
        else:
            return None

    @staticmethod
    def _initialise_database(database_url):
        engine = sqlalchemy.create_engine(database_url)
        metadata = sqlalchemy.MetaData(bind=engine)
        # Using Text for storing JSON data since sqlalchemy.types.JSON is not
        # supported on all database platforms yet.
        sqlalchemy.Table(
            'flow', metadata,
            sqlalchemy.Column('uuid', sqlalchemy.String(36), primary_key=True),
            sqlalchemy.Column('json', sqlalchemy.Text)
        )
        sqlalchemy.Table(
            'contact', metadata,
            sqlalchemy.Column('uuid', sqlalchemy.String(36), primary_key=True),
            sqlalchemy.Column('json', sqlalchemy.Text)
        )
        sqlalchemy.Table(
            'flowrun', metadata,
            sqlalchemy.Column('run', sqlalchemy.Integer, primary_key=True),
            sqlalchemy.Column('json', sqlalchemy.Text),
            sqlalchemy.Column('flow_uuid', sqlalchemy.ForeignKey('flow.uuid')),
            sqlalchemy.Column('contact_uuid',
                              sqlalchemy.ForeignKey('contact.uuid'))
        )
        metadata.create_all()
        return metadata

    def _insert_object(self, rapidpro_object):
        if isinstance(rapidpro_object, temba_client.v1.types.Run):
            exists = self._flowruns.select(sqlalchemy.exists().where(
                self._flowruns.c.run == rapidpro_object.id))
            insert = self._flowruns.insert()
            record = {
                'run': rapidpro_object.id,
                'json': json.dumps(rapidpro_object.serialize()),
                'contact_uuid': rapidpro_object.contact,
                'flow_uuid': rapidpro_object.flow
            }
        elif isinstance(rapidpro_object, temba_client.v1.types.Flow):
            exists = self._flows.select(sqlalchemy.exists().where(
                self._flows.c.uuid == rapidpro_object.uuid))
            insert = self._flows.insert()
            record = {
                'uuid': rapidpro_object.uuid,
                'json': json.dumps(rapidpro_object.serialize()),
            }
        elif isinstance(rapidpro_object, temba_client.v1.types.Contact):
            exists = self._contacts.select(sqlalchemy.exists().where(
                self._contacts.c.uuid == rapidpro_object.uuid))
            insert = self._contacts.insert()
            record = {
                'uuid': rapidpro_object.uuid,
                'json': json.dumps(rapidpro_object.serialize()),
            }
        else:
            raise TypeError(self.INVALID_TYPE.format(type(rapidpro_object)))
        if not self.database.bind.execute(exists).scalar():
            self.database.bind.execute(insert, record)

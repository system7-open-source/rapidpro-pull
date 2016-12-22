# coding=utf-8
# noinspection PyPackageRequirements
import sqlalchemy.ext.declarative
# noinspection PyPackageRequirements
import sqlalchemy.orm

from base import *
# noinspection PyPackageRequirements
from behave import *

use_step_matcher("re")

Base = sqlalchemy.ext.declarative.declarative_base()


class Contact(Base):
    __tablename__ = 'contact'
    uuid = sqlalchemy.Column(sqlalchemy.String(36), primary_key=True)
    json = sqlalchemy.Column(sqlalchemy.Text)


class Flow(Base):
    __tablename__ = 'flow'
    uuid = sqlalchemy.Column(sqlalchemy.String(36), primary_key=True)
    json = sqlalchemy.Column(sqlalchemy.Text)


class FlowRun(Base):
    __tablename__ = 'flowrun'
    run = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    json = sqlalchemy.Column(sqlalchemy.Text)
    flow_uuid = sqlalchemy.Column(sqlalchemy.String(36),
                                  sqlalchemy.ForeignKey('flow.uuid'))
    flow = sqlalchemy.orm.relationship(Flow)
    contact_uuid = sqlalchemy.Column(sqlalchemy.String(36),
                                     sqlalchemy.ForeignKey('contact.uuid'))
    contact = sqlalchemy.orm.relationship(Contact)


def get_new_session(database_url):
    # database
    database_engine = sqlalchemy.create_engine(database_url)
    Base.metadata.bind = database_engine
    db_session_class = sqlalchemy.orm.sessionmaker(bind=database_engine)
    return db_session_class()


def get_db_class(object_type):
    object_type = object_type.lower()
    if 'run' in object_type:
        return FlowRun
    elif object_type.startswith('flow'):
        return Flow
    elif object_type.startswith('contact'):
        return Contact
    else:
        raise ValueError('Unknown object type "{}".'.format(object_type))


@step('the following objects are already stored in the provided cache'
      ' "(?P<db_url>.+)"')
def step_impl(context, db_url):
    """
    :type context: behave.runner.Context
    :type db_url: str
    """
    context.database_url = db_url
    database_engine = sqlalchemy.create_engine(context.database_url)
    Base.metadata.bind = database_engine
    Base.metadata.drop_all(database_engine)
    Base.metadata.create_all(database_engine)
    db_session_class = sqlalchemy.orm.sessionmaker(bind=database_engine)
    session = db_session_class()
    objects = context.test_utilities.Auxiliary.make_objects(context.table)
    context.cached_objects = objects
    flows = {}
    contacts = {}
    for object_type in ['flows', 'contacts']:
        for o in objects[object_type]:
            object_json = json.dumps(o.serialize())
            if object_type == 'flows':
                new_record = Flow(uuid=o.uuid, json=object_json)
                flows[o.uuid] = new_record
            else:
                new_record = Contact(uuid=o.uuid, json=object_json)
                contacts[o.uuid] = new_record
            session.add(new_record)
            session.commit()
    for fr in objects['flow runs']:
        fr_json = json.dumps(fr.serialize())
        session.add(FlowRun(run=fr.id, json=fr_json,
                            flow_uuid=fr.flow, contact_uuid=fr.contact))
        session.commit()


@step('the provided cache now contains table "(?P<table>.+)" with'
      ' "(?P<ids>.*)"')
def step_impl(context, table, ids):
    """
    :type context: behave.runner.Context
    :type table: str
    :type ids: str
    """
    # expected
    expected_ids = [str(s.strip()) for s in ids.split(',') if s]
    db_class = get_db_class(table)
    if table == 'flowrun':
        expected_ids = map(int, expected_ids)
    elif table not in ['contact', 'flow']:
        raise ValueError('Unsupported table "{}"'.format(table))
    # initialise database
    session = get_new_session(context.database_url)
    # observed
    for pk in expected_ids:
        assert_that(
            session.query(db_class).get(pk), is_not(None),
            'pk "{pk}" not found in table "{table}"'.format(pk=pk, table=table))


@then("the program prints a valid JSON document containing requested"
      " (?P<object_type>.+) with previously cached substituted for their"
      " downloadable counterparts")
def step_impl(context, object_type):
    """
    :type context: behave.runner.Context
    :type object_type: str
    """
    # expected objects
    indexed_remote_objects = context.test_utilities.Auxiliary.\
        index_objects_by_id(context.remote_objects)
    indexed_cached_objects = context.test_utilities.Auxiliary. \
        index_objects_by_id(context.cached_objects)
    context.uncached_objects = {}
    for k in indexed_remote_objects:
        context.uncached_objects[k] = [
            indexed_remote_objects[k][kk]
            for kk in indexed_remote_objects[k]
            if kk not in indexed_cached_objects[k]]
        indexed_remote_objects[k].update(indexed_cached_objects[k])
    context.expected_objects = {
        k: indexed_remote_objects[k].values() for k in indexed_remote_objects}
    expected_json = [o.serialize()
                     for o in context.expected_objects[object_type]]
    # output
    assert_that(context.stderr, empty())
    result_objects = json.loads(context.stdout)
    # test
    if len(expected_json) == 0:
        assert_that(result_objects, empty())
    else:
        assert_that(result_objects, contains_inanyorder(*expected_json))


@step("the provided cache still contains all the previously cached objects"
      " unchanged")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    # expected
    expected_json = {}
    for k in context.cached_objects:
        expected_json[k] = [o.serialize() for o in context.cached_objects[k]]
    # initialise database
    session = get_new_session(context.database_url)
    # observed
    in_cache = {}
    for k in expected_json:
        db_class = get_db_class(k)
        in_cache[k] = [json.loads(o.json)
                       for o in session.query(db_class).all()]
        assert_that(in_cache[k], has_items(*expected_json[k]))


@step("the provided cache now also contains all previously uncached"
      " (?P<object_type>.+)")
def step_impl(context, object_type):
    """
    :type context: behave.runner.Context
    :type object_type: str
    """
    # expected
    expected_json = [o.serialize()
                     for o in context.uncached_objects[object_type]]
    # initialise database
    session = get_new_session(context.database_url)
    # observed
    db_class = get_db_class(object_type)
    in_cache = [json.loads(o.json) for o in session.query(db_class).all()]
    assert_that(in_cache, has_items(*expected_json))


@step("the number of objects in cache is the sum of the previously cached"
      " objects and the previously uncached (?P<object_type>.+)")
def step_impl(context, object_type):
    """
    :type context: behave.runner.Context
    :type object_type: str
    """
    # expected
    cached = sum([len(context.cached_objects[k])
                  for k in context.cached_objects])
    uncached = len(context.uncached_objects[object_type])
    expected_number_of_objects_in_cache = cached + uncached
    # initialise database
    session = get_new_session(context.database_url)
    # observed
    number_of_objects_in_cache = 0
    for k in context.cached_objects:
        db_class = get_db_class(k)
        number_of_objects_in_cache += session.query(db_class).count()
    assert_that(number_of_objects_in_cache,
                equal_to(expected_number_of_objects_in_cache))

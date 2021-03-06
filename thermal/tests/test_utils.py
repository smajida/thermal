import os
from mock import ANY, call, Mock, patch
import uuid

import boto
from flask import current_app
import pytest

import conftest
from thermal.exceptions import DocumentConfigurationError, NotFoundError
import thermal.utils as tu


class TestUtilsUnit(object):

    def test_get_paging_info_from_args_dict_returns_ok_with_good_paging_info(self):
        args_dict = {'page_number': '1', 'items_per_page': '2'}

        (paging_requested, start_index, end_index) = tu.get_paging_info_from_args_dict(args_dict)
        assert paging_requested
        assert start_index == 0
        assert end_index == 1

    def test_get_paging_info_from_args_dict_fails_with_nonnumeric_page_number(self):
        args_dict = {'page_number': 'x', 'items_per_page': '2'}
        with pytest.raises(DocumentConfigurationError) as exception_info:
            (paging_requested, start_index, end_index) = tu.get_paging_info_from_args_dict(args_dict)
        assert 'invalid number specified for page_number' in str(exception_info.value)

    def test_get_paging_from_args_dict_info_fails_with_negative_page_number(self):
        args_dict = {'page_number': '-1', 'items_per_page': '2'}
        with pytest.raises(DocumentConfigurationError) as exception_info:
            (paging_requested, start_index, end_index) = tu.get_paging_info_from_args_dict(args_dict)
        assert 'page_number must be a number greater than zero' in str(exception_info.value)

    def test_get_paging_info_from_args_dict_fails_with_nonnumeric_items_per_page(self):
        args_dict = {'page_number': '1', 'items_per_page': 'x'}
        with pytest.raises(DocumentConfigurationError) as exception_info:
            (paging_requested, start_index, end_index) = tu.get_paging_info_from_args_dict(args_dict)
        assert 'invalid number specified for items_per_page' in str(exception_info.value)

    def test_get_paging_info_from_args_dict_fails_with_negative_items_per_page(self):
        args_dict = {'page_number': '1', 'items_per_page': '-2'}
        with pytest.raises(DocumentConfigurationError) as exception_info:
            (paging_requested, start_index, end_index) = tu.get_paging_info_from_args_dict(args_dict)
        assert 'items_per_page must be a number greater than zero' in str(exception_info.value)

    def test_doc_attribute_can_be_set_works_for_normal_and_forbidden_keys(self):
        assert tu.doc_attribute_can_be_set('lester')
        assert not tu.doc_attribute_can_be_set('_id')
        assert not tu.doc_attribute_can_be_set('_rev')

    def test_get_parameter_fetches_parameter_when_all_is_well(self):
        with current_app.test_request_context('/whatever?the_parameter=the_value'):
            from flask import request  # I know, crazy, but you need to import request here, not at the top of the module
            assert 'the_parameter' in request.args
            fetched_value = tu._get_parameter('the_parameter')
            assert fetched_value == 'the_value'

    def test_get_parameter_fetches_None_when_no_parameter_and_no_default(self):
        with current_app.test_request_context('/whatever?the_parameter=the_value'):
            fetched_value = tu._get_parameter('mike_ptyson')
            assert fetched_value == None

    def test_get_parameter_fetches_default_when_no_parameter_and_default_specified(self):
        with current_app.test_request_context('/whatever?the_parameter=the_value'):
            fetched_value = tu._get_parameter('mike_ptyson', default='john_abercrombie')
            assert fetched_value == 'john_abercrombie'

    def test_get_parameter_returns_string_by_default(self):
        with current_app.test_request_context('/whatever?the_parameter=66'):
            fetched_value = tu._get_parameter('the_parameter')
            assert type(fetched_value).__name__ == 'unicode'
            assert fetched_value == '66'

    def test_get_parameter_can_cast_a_value_to_int(self):
        with current_app.test_request_context('/whatever?the_parameter=66'):
            fetched_value = tu._get_parameter('the_parameter', cast_function=int)
            assert type(fetched_value).__name__ == 'int'
            assert fetched_value == 66

    def test_get_parameter_returns_none_when_cast_fails_and_no_default_and_no_raise_value_error(self):
        with current_app.test_request_context('/whatever?the_parameter=baloney'):
            fetched_value = tu._get_parameter('the_parameter', cast_function=int)
            assert fetched_value == None

    def test_get_parameter_returns_default_when_cast_fails_and_default_specified_and_no_raise_value_error(self):
        with current_app.test_request_context('/whatever?the_parameter=baloney'):
            fetched_value = tu._get_parameter('the_parameter', default='monkey_chow', cast_function=int)
            assert fetched_value == 'monkey_chow'

    def test_get_parameter_raises_valueerror_when_cast_fails_and_default_specified_and_raise_value_error_requested(self):
        with current_app.test_request_context('/whatever?the_parameter=baloney'):
            with pytest.raises(ValueError) as exception_info:
                fetched_value = tu._get_parameter('the_parameter', default='monkey_chow', cast_function=int, raise_value_error=True)
            assert 'problem casting parameter the_parameter (value baloney) as type int' in str(exception_info.value)

    def test_gather_and_enforce_request_args_enumerated_throws_dce_when_no_name_supplied(self):
        with current_app.test_request_context('/whatever?yoo=hoo'):
            with pytest.raises(DocumentConfigurationError) as exception_info:
                fetched_value = tu.gather_and_enforce_request_args_enumerated([{'required': True}])
            assert 'bad call to gather_and_enforce_request_args: no name supplied' in str(exception_info.value)

    def test_gather_and_enforce_request_args_enumerated_throws_dce_when_parm_required_and_absent(self):
        with current_app.test_request_context('/whatever?yoo=hoo'):
            with pytest.raises(DocumentConfigurationError) as exception_info:
                fetched_value = tu.gather_and_enforce_request_args_enumerated([{'name': 'a', 'required': True}])
            assert 'required parameter a not supplied in request' in str(exception_info.value)

    def test_gather_and_enforce_request_args_enumerated_gets_parm_when_parm_required_and_present(self):
        with current_app.test_request_context('/whatever?c=d'):
            fetched_value = tu.gather_and_enforce_request_args_enumerated([{'name': 'c', 'required': True}])
            assert fetched_value == {'c': 'd'}

    def test_gather_and_enforce_request_args_enumerated_gets_parm_when_parm_optional_and_present(self):
        with current_app.test_request_context('/whatever?party=started'):
            fetched_value = tu.gather_and_enforce_request_args_enumerated([{'name': 'party'}])
            assert fetched_value == {'party': 'started'}

    def test_gather_and_enforce_request_args_enumerated_gets_default_when_parm_optional_and_absent_and_default(self):
        with current_app.test_request_context('/whatever'):
            fetched_value = tu.gather_and_enforce_request_args_enumerated([{'name': 'hammer', 'default': 'dont_hurt_em'}])
            assert fetched_value == {'hammer': 'dont_hurt_em'}

    def test_gather_and_enforce_request_args_enumerated_gets_nothing_when_parm_optional_and_absent_and_no_default(self):
        with current_app.test_request_context('/whatever'):
            fetched_value = tu.gather_and_enforce_request_args_enumerated([{'name': 'vanilla'}])
            assert fetched_value == {}

    def test_gather_and_enforce_request_args_enumerated_passes_error_when_cast_fails(self):
        with current_app.test_request_context('/whatever?yoo=hoo'):
            with pytest.raises(ValueError) as exception_info:
                fetched_value = tu.gather_and_enforce_request_args_enumerated([{'name': 'yoo', 'cast_function': int}])
            assert 'problem casting parameter yoo (value hoo) as type int' in str(exception_info.value)

    @patch('thermal.utils._get_parameter')
    def test_gather_and_enforce_request_args_enumerated_defaults_values_for_default_cast_function_and_raise_value(self,
                                                                                                                  tu_get_parm):
        tu_get_parm.return_value = 'ice'
        with current_app.test_request_context('/whatever?vanilla=ice'):
            fetched_value = tu.gather_and_enforce_request_args_enumerated([{'name': 'vanilla'}])
            assert fetched_value == {'vanilla': 'ice'}
            assert tu_get_parm.called_once_with('vanilla', default=None, cast_function=None, raise_value_error=True)

    @patch('thermal.utils.gather_and_enforce_request_args_enumerated')
    def test_gather_and_enforce_request_args_any_searchable_calls_gaera_enum(self,
                                                                             tu_gather_and_enforce_request_args_enum):
        tu_gather_and_enforce_request_args_enum.return_value = {'page_number': 3, 'items_per_page': 4}
        with current_app.test_request_context('/whatever?page_number=1&items_per_page=2'):
            ret_val = tu.gather_and_enforce_request_args_any_searchable()

            the_call = call([{'name': 'page_number',
                              'default': 0,
                              'cast_function': int,
                              'required': False},
                              {'name': 'items_per_page',
                              'default': 0,
                              'cast_function': int,
                              'required': False}])
            tu_gather_and_enforce_request_args_enum.assert_has_calls([the_call])
            assert ret_val == {'page_number': 3, 'items_per_page': 4}

    @patch('thermal.utils.gather_and_enforce_request_args_any_searchable')
    def test_gather_and_enforce_request_args_routes_to_gaera_any_searchable(self,
                                                                            tu_gather_and_enforce_request_args_any_searchable):
        tu_gather_and_enforce_request_args_any_searchable.return_value = {'a': 'b'}
        with current_app.test_request_context('/whatever'):
            ret_val = tu.gather_and_enforce_request_args(['ANY_SEARCHABLE'])
            tu_gather_and_enforce_request_args_any_searchable.assert_called_once_with()

    @patch('thermal.utils.gather_and_enforce_request_args_enumerated')
    def test_gather_and_enforce_request_args_routes_to_gaera_enumerated(self,
                                                                        tu_gather_and_enforce_request_args_enumerated):
        tu_gather_and_enforce_request_args_enumerated.return_value = {'c': 'd'}
        with current_app.test_request_context('/whatever'):
            ret_val = tu.gather_and_enforce_request_args([{'name': 'steve'}])
            tu_gather_and_enforce_request_args_enumerated.assert_called_once_with([{'name': 'steve'}])


class TestUtilsIntegration(object):

    def test_gather_and_enforce_request_args_any_searchable_gets_page_info_when_present(self):
        with current_app.test_request_context('/whatever?page_number=1&items_per_page=2&something=else'):
            ret_val = tu.gather_and_enforce_request_args_any_searchable()
            assert ret_val == {'page_number': 1, 'items_per_page': 2, 'something': 'else'}

    def test_gather_and_enforce_request_args_any_searchable_gets_zeroed_out_page_info_when_not_present(self):
        with current_app.test_request_context('/whatever'):
            ret_val = tu.gather_and_enforce_request_args_any_searchable()
            assert ret_val == {'page_number': 0, 'items_per_page': 0}

    def test_get_documents_from_criteria_fetches_by_arbitrary_criterion(self):
        id_1 = str(uuid.uuid4())
        the_doc = {'doctor': 'strangelove'}
        current_app.db[id_1] = the_doc
        id_2 = str(uuid.uuid4())
        the_doc = {'doctor': 'demento'}
        current_app.db[id_2] = the_doc
        id_3 = str(uuid.uuid4())
        the_doc = {'doctor': 'detroit'}
        current_app.db[id_3] = the_doc
        args_dict = {'doctor': 'demento'}

        documents = tu.get_documents_from_criteria(args_dict)

        assert len(documents.keys()) == 1
        assert id_2 in documents

    def test_get_documents_from_criteria_recognizes_gallery_url_not_noll_kwarg(self):
        id_1 = str(uuid.uuid4())
        the_doc = {'doctor': 'strangelove', 'gallery_url': 'something'}
        current_app.db[id_1] = the_doc
        id_2 = str(uuid.uuid4())
        the_doc = {'doctor': 'strangelove'}
        current_app.db[id_2] = the_doc

        args_dict = {'doctor': 'strangelove', 'gallery_url_not_null': True}

        documents = tu.get_documents_from_criteria(args_dict)

        assert len(documents.keys()) == 1
        assert id_1 in documents

    def test_item_exists_returns_true_when_item_exists_type_specific(self):
        item_id = uuid.uuid4()
        doc_1 = {
            '_id': str(item_id),
            'type': 'picture'
        }
        tu.save_document(doc_1)

        assert tu.item_exists(item_id, 'picture')

    def test_item_exists_returns_true_when_item_exists_type_any(self):
        item_id = uuid.uuid4()
        doc_1 = {
            '_id': str(item_id),
            'type': 'picture'
        }
        tu.save_document(doc_1)

        assert tu.item_exists(item_id, 'any')

    def test_item_exists_returns_false_when_item_exists_but_doesnt_match_type(self):
        item_id = uuid.uuid4()
        doc_1 = {
            '_id': str(item_id),
            'type': 'picture'
        }
        tu.save_document(doc_1)

        assert not tu.item_exists(item_id, 'exterminator')

    def test_item_exists_returns_false_when_item_doesnt_exist_type_any(self):
        item_id = uuid.uuid4()

        assert not tu.item_exists(item_id, 'any')

    def test_save_document_works_when_document_is_complete(self):
        doc_id = uuid.uuid4()
        dict_in = {'_id': doc_id,
                   'type': 'wookie'}
        tu.save_document(dict_in)

        assert tu.item_exists(doc_id, 'any')

    def test_save_document_casts_id_to_string(self):
        doc_id = uuid.uuid4()
        dict_in = {'_id': doc_id,
                   'type': 'wookie'}
        tu.save_document(dict_in)

        the_retrieved_doc = current_app.db[str(doc_id)]
        assert type(the_retrieved_doc['_id']).__name__ == 'unicode'

    def test_save_document_removes_dynamically_calculated_attributes(self):
        doc_id = uuid.uuid4()
        dict_in = {'_id': doc_id,
                   'type': 'wookie'}
        one_dynamic_attr_name = tu.dynamically_calculated_attributes[0]
        dict_in[one_dynamic_attr_name] = 'something'
        tu.save_document(dict_in)

        the_saved_doc = current_app.db[str(doc_id)]

        assert one_dynamic_attr_name not in the_saved_doc

    def test_save_document_fails_when_no_id(self):
        dict_in = {'type': 'wookie'}
        with pytest.raises(DocumentConfigurationError) as exception_info:
            tu.save_document(dict_in)

        assert 'trying to save the document with no id' in str(exception_info.value)

    def test_save_document_fails_when_no_type(self):
        doc_id = uuid.uuid4()
        dict_in = {'_id': doc_id}
        with pytest.raises(DocumentConfigurationError) as exception_info:
            tu.save_document(dict_in)

        error_string = 'trying to save the document with no value for type: {0}'.format(str(doc_id))
        assert error_string in str(exception_info.value)

    def test_get_singleton_document_fails_when_zero_documents_exist(self):
        doc_id = uuid.uuid4()
        dict_in = {'_id': doc_id,
                   'type': 'twix'}
        tu.save_document(dict_in)
        with pytest.raises(NotFoundError) as exception_info:
            tu.get_singleton_document('skittles')

        error_string = 'no document found of type skittles, expected singleton'
        assert error_string in str(exception_info.value)

    def test_get_singleton_document_fails_when_more_than_one_documents_exist(self):
        tu.save_document({'_id': uuid.uuid4(), 'type': 'marathon'})
        tu.save_document({'_id': uuid.uuid4(), 'type': 'marathon'})
        with pytest.raises(DocumentConfigurationError) as exception_info:
            tu.get_singleton_document('marathon')

        error_string = 'more than one document found of type marathon, expected singleton'
        assert error_string in str(exception_info.value)

    def test_get_singleton_document_succeeds_when_one_document_is_found(self):
        doc_id = uuid.uuid4()
        tu.save_document({'_id': doc_id, 'type': 'zagnut'})
        the_dict = tu.get_singleton_document('zagnut')

        assert the_dict
        assert the_dict['_id'] == str(doc_id)

    def test_get_document_fetches_a_document_with_the_proper_id_supplied_as_string(self):
        doc_id = str(uuid.uuid4())
        tu.save_document({'_id': doc_id, 'type': 'zagnut'})
        the_dict = tu.get_document(doc_id)

        assert the_dict
        assert the_dict['_id'] == doc_id

    def test_get_document_fetches_a_document_with_the_proper_id_supplied_as_uuid(self):
        doc_id = uuid.uuid4()
        tu.save_document({'_id': doc_id, 'type': 'zagnut'})
        the_dict = tu.get_document(doc_id)

        assert the_dict
        assert the_dict['_id'] == str(doc_id)

    def test_get_document_returns_none_when_document_not_found(self):
        doc_id = uuid.uuid4()
        the_dict = tu.get_document(doc_id)

        assert not the_dict

    def test_get_document_with_exception_throws_exception_when_document_of_specified_type_doesnt_exist(self):
        doc_id = uuid.uuid4()
        dict_in = {'_id': doc_id,
                   'type': 'twix'}
        tu.save_document(dict_in)
        with pytest.raises(NotFoundError) as exception_info:
            tu.get_document_with_exception(doc_id, document_type='skittles')

        error_string = 'No document of type skittles found for id {0}'.format(str(doc_id))
        assert error_string in str(exception_info.value)

    def test_get_document_with_exception_throws_exception_when_no_document_of_any_type_exists_for_requested_id(self):
        doc_id = uuid.uuid4()
        dict_in = {'_id': doc_id,
                   'type': 'twix'}
        tu.save_document(dict_in)
        second_doc_id = uuid.uuid4()
        with pytest.raises(NotFoundError) as exception_info:
            tu.get_document_with_exception(second_doc_id)

        error_string = 'No document of type any found for id {0}'.format(str(second_doc_id))
        assert error_string in str(exception_info.value)

import json
from mock import ANY, call, Mock, patch
import pytest
import uuid

from flask import current_app, request

import admin.views as av
from thermal.exceptions import DocumentConfigurationError, NotFoundError


# TODO this needs a ton more tests
class TestViewsUnit(object):
    @patch('admin.views.find_pictures')
    @patch('admin.views.get_group_document')
    def test_get_paging_info_gets_needed_params(self,
                                                av_get_group_document,
                                                av_find_pictures):
        av_get_group_document.return_value = {'_id': '3145'}
        av_find_pictures.return_value = {'y': 'b'}
        with current_app.test_client() as c:
            resp_object = c.get('/api/v1/admin/groups/xxx/pictures?page=2&items_per_page=44')
            av_get_group_document.assert_called_with('xxx')
            the_call = call({'group_id':'3145'}, page='2', items_per_page='44')
            av_find_pictures.assert_has_calls([the_call])
            response_data_dict = json.loads(resp_object.data)
            assert request.args['page'] == '2'
            assert request.args['items_per_page'] == '44'
            assert resp_object.status_code == 200
            assert 'y' in response_data_dict
            assert len(response_data_dict.keys()) == 1


    @patch('admin.views.get_settings_document')
    def test_get_settings_calls_get_settings_document(self,
                                                      av_get_settings_document):
        av_get_settings_document.return_value = {'h': 't'}

        resp_object = av.get_settings()
        response_data_dict = json.loads(resp_object.data)

        av_get_settings_document.assert_called_once_with()
        assert resp_object.status_code == 200
        assert 'h' in response_data_dict
        assert len(response_data_dict.keys()) == 1


    @patch('admin.views.save_document')
    @patch('admin.views.get_settings_document')
    def test_update_settings_fails_when_bad_content_type(self,
                                                         av_get_settings_document,
                                                         av_save_document):
        av_get_settings_document.return_value = {'starfish': 'patrick'}
        with current_app.test_client() as c:
            resp_object = c.put('/api/v1/admin/settings',content_type='spongey')
            assert resp_object.data == '"no valid settings parameters supplied"'
            assert resp_object.status_code == 409


# TODO get this test working
#    @patch('admin.views.save_document')
#    @patch('admin.views.doc_attribute_can_be_set')
#    @patch('admin.views.get_settings_document')
#    def test_update_settings_sets_allowed_values(self,
#                                                 av_get_settings_document,
#                                                 av_doc_attribute_can_be_set,
#                                                 av_save_document):
#        av_get_settings_document.return_value = {'starfish': 'patrick'}
#        av_doc_attribute_can_be_set.return_value = True
#        with current_app.test_client() as c:
#            haha = 'joe'
#            resp_object = c.put('/api/v1/admin/settings', json=dict(current_group_id=haha), content_type='application/json')
#            assert resp_object.status_code == 200


    @patch('admin.views.get_group_document_with_child_objects')
    @patch('admin.views.get_group_document_with_child_links')
    @patch('admin.views.get_group_document')
    def test_get_group_calls_get_group_document_when_group_found(self,
                                                                 av_get_group_document,
                                                                 av_get_group_document_with_child_links,
                                                                 av_get_group_document_with_child_objects):
        av_get_group_document.return_value = {'v': 'm'}
        resp_object = current_app.test_client().get('/api/v1/admin/groups/123321')
        response_data_dict = json.loads(resp_object.data)

        av_get_group_document.assert_called_once_with('123321')
        av_get_group_document_with_child_links.assert_not_called()
        av_get_group_document_with_child_objects.assert_not_called()
        assert resp_object.status_code == 200
        assert 'v' in response_data_dict
        assert len(response_data_dict.keys()) == 1

    @patch('admin.views.get_group_document_with_child_objects')
    @patch('admin.views.get_group_document_with_child_links')
    @patch('admin.views.get_group_document')
    def test_get_group_fails_when_group_not_found(self,
                                                  av_get_group_document,
                                                  av_get_group_document_with_child_links,
                                                  av_get_group_document_with_child_objects):
        av_get_group_document.side_effect = NotFoundError('no group document found for 4422')
        resp_object = current_app.test_client().get('/api/v1/admin/groups/4422')
        av_get_group_document.assert_called_once_with('4422')
        assert resp_object.status_code == 404
        assert resp_object.data == '"no group document found for 4422"'


    @patch('admin.views.get_group_document_with_child_objects')
    @patch('admin.views.get_group_document_with_child_links')
    @patch('admin.views.get_group_document')
    def test_get_group_gets_child_links_when_requested(self,
                                                       av_get_group_document,
                                                       av_get_group_document_with_child_links,
                                                       av_get_group_document_with_child_objects):
        av_get_group_document_with_child_links.return_value = {'r': 'q'}
        with current_app.test_client() as c:
            resp_object = c.get('/api/v1/admin/groups/123321?child_links=x')
            av_get_group_document.assert_not_called()
            av_get_group_document_with_child_links.assert_called_once_with('123321')
            av_get_group_document_with_child_objects.assert_not_called()
            response_data_dict = json.loads(resp_object.data)
            assert request.args['child_links'] == 'x'
            assert resp_object.status_code == 200
            assert 'r' in response_data_dict
            assert len(response_data_dict.keys()) == 1


    @patch('admin.views.get_group_document_with_child_objects')
    @patch('admin.views.get_group_document_with_child_links')
    @patch('admin.views.get_group_document')
    def test_get_group_gets_child_objects_when_requested(self,
                                                         av_get_group_document,
                                                         av_get_group_document_with_child_links,
                                                         av_get_group_document_with_child_objects):
        av_get_group_document_with_child_objects.return_value = {'m': 's'}
        with current_app.test_client() as c:
            resp_object = c.get('/api/v1/admin/groups/123321?child_objects=x')
            av_get_group_document.assert_not_called()
            av_get_group_document_with_child_links.assert_not_called()
            av_get_group_document_with_child_objects.assert_called_once_with('123321')
            response_data_dict = json.loads(resp_object.data)
            assert request.args['child_objects'] == 'x'
            assert resp_object.status_code == 200
            assert 'm' in response_data_dict
            assert len(response_data_dict.keys()) == 1


    @patch('admin.views.get_group_document_with_child_objects')
    @patch('admin.views.get_group_document_with_child_links')
    @patch('admin.views.get_group_document')
    def test_get_group_gets_child_objects_when_both_links_and_objects_are_requested(self,
                                                                                    av_get_group_document,
                                                                                    av_get_group_document_with_child_links,
                                                                                    av_get_group_document_with_child_objects):
        av_get_group_document_with_child_objects.return_value = {'o': 'i'}
        with current_app.test_client() as c:
            resp_object = c.get('/api/v1/admin/groups/123321?child_objects=x&child_links=y')
            av_get_group_document.assert_not_called()
            av_get_group_document_with_child_links.assert_not_called()
            av_get_group_document_with_child_objects.assert_called_once_with('123321')
            response_data_dict = json.loads(resp_object.data)
            assert request.args['child_objects'] == 'x'
            assert request.args['child_links'] == 'y'
            assert resp_object.status_code == 200
            assert 'o' in response_data_dict
            assert len(response_data_dict.keys()) == 1


    @patch('admin.views.find_pictures')
    @patch('admin.views.get_paging_info_from_request')
    @patch('admin.views.get_group_document')
    def test_get_group_pictures_calls_appropriate_methods(self,
                                                          av_get_group_document,
                                                          av_get_paging_info_from_request,
                                                          av_find_pictures):
        av_get_group_document.return_value = {'_id': '123'}
        av_get_paging_info_from_request.return_value = (2, 3)
        av_find_pictures.return_value = {'some_key': 'some_value'}

        resp_object = av.get_group_pictures('current')
        response_data_dict = json.loads(resp_object.data)

        av_get_group_document.assert_called_once_with('current')
        av_find_pictures.assert_called_once_with({'group_id': '123'}, page=2, items_per_page=3)
        assert resp_object.status_code == 200
        assert 'some_key' in response_data_dict
        assert len(response_data_dict.keys()) == 1

    @patch('admin.views.find_pictures')
    @patch('admin.views.get_paging_info_from_request')
    @patch('admin.views.get_group_document')
    def test_get_group_pictures_handles_crash_in_find_pictures(self,
                                                               av_get_group_document,
                                                               av_get_paging_info_from_request,
                                                               av_find_pictures):
        av_get_group_document.return_value = {'_id': '123'}
        av_get_paging_info_from_request.return_value = (2, 'irish')
        av_find_pictures.side_effect = DocumentConfigurationError('invalid number specified for items_per_page: irish')

        resp_object = av.get_group_pictures('current')

        av_find_pictures.assert_called_once_with({'group_id': '123'}, page=2, items_per_page='irish')
        assert resp_object.status_code == 409
        assert resp_object.data == '"invalid number specified for items_per_page: irish"'

    @patch('admin.views.find_pictures')
    @patch('admin.views.get_paging_info_from_request')
    @patch('admin.views.get_group_document')
    def test_get_group_gallery_calls_appropriate_methods(self,
                                                         av_get_group_document,
                                                         av_get_paging_info_from_request,
                                                         av_find_pictures):
        av_get_group_document.return_value = {'_id': '123'}
        av_get_paging_info_from_request.return_value = (2, 3)
        av_find_pictures.return_value = {'some_key': 'some_value'}

        resp_object = av.get_group_gallery('current')
        response_data_dict = json.loads(resp_object.data)

        av_get_group_document.assert_called_once_with('current')
        av_find_pictures.assert_called_once_with({'group_id': '123'}, gallery_url_not_null=True, page=2, items_per_page=3)
        assert resp_object.status_code == 200
        assert 'some_key' in response_data_dict
        assert len(response_data_dict.keys()) == 1

    @patch('admin.views.find_pictures')
    @patch('admin.views.get_paging_info_from_request')
    @patch('admin.views.get_group_document')
    def test_get_group_gallery_handles_crash_in_find_pictures(self,
                                                              av_get_group_document,
                                                              av_get_paging_info_from_request,
                                                              av_find_pictures):
        av_get_group_document.return_value = {'_id': '123'}
        av_get_paging_info_from_request.return_value = (2, 'irish')
        av_find_pictures.side_effect = DocumentConfigurationError('invalid number specified for items_per_page: irish')

        resp_object = av.get_group_gallery('current')

        av_find_pictures.assert_called_once_with({'group_id': '123'}, gallery_url_not_null=True, page=2, items_per_page='irish')
        assert resp_object.status_code == 409
        assert resp_object.data == '"invalid number specified for items_per_page: irish"'


# TODO this will need an integration test because that gallery_url_not_null is a little special
# @admin.route('/groups/<group_id>/gallery', methods=['GET'])

# TODO make a unit test when I figure out how to mock out the request headers and request.json.keys
# @admin.route('/groups/<group_id>', methods=['PUT'])
# def update_group(group_id):
#     group_dict = get_group_document(group_id)
#     if request.headers['Content-Type'] == 'application/json':
#         for k in request.json.keys():
#             if doc_attribute_can_be_set(k):
#                 group_dict[k] = request.json[k]
#         save_document(group_dict)
#         return Response(json.dumps(group_dict), status=200, mimetype='application/json')

# TODO make a unit test when I figure out how to mock out the request headers and request.json.keys
# @admin.route('/groups', methods=['POST'])
# def save_group():
#     settings = get_settings_document()
#     group_dict = default_group_dict()
#     if request.headers['Content-Type'] == 'application/json':
#         for k in request.json.keys():
#             if doc_attribute_can_be_set(k):
#                 group_dict[k] = request.json[k]
#         save_document(group_dict)
#         settings['current_group_id'] = group_dict['_id']
#         save_document(settings)
#         return Response(json.dumps(group_dict), status=200, mimetype='application/json')

    def test_doc_attribute_can_be_set_works_for_normal_and_forbidden_keys(self):
        assert av.doc_attribute_can_be_set('lester')
        assert not av.doc_attribute_can_be_set('_id')
        assert not av.doc_attribute_can_be_set('_rev')

#class TestViewsIntegration(object):

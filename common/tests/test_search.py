import json

from django.test import TestCase
from django.core.urlresolvers import reverse

from model_mommy import mommy

from facilities.models import Facility
from facilities.serializers import FacilitySerializer
from common.tests import ViewTestBase

from ..filters.filter_shared import SearchFilter

from ..utilities import search_utils


class TestElasticSearchAPI(TestCase):
    def setUp(self):
        self.elastic_search_api = search_utils.ElasticAPI()
        super(TestElasticSearchAPI, self).setUp()

    def tearDown(self):
        self.elastic_search_api.delete_index(index_name='test_index')
        super(TestElasticSearchAPI, self).tearDown()

    def test_setup_index(self):
        self.elastic_search_api.delete_index(index_name='test_index')
        result = self.elastic_search_api.setup_index(index_name='test_index')
        self.assertEquals(200, result.status_code)
        self.elastic_search_api.delete_index(index_name='test_index')

    def test_get_index_does_not_exists(self):
        index_name = 'test_index'
        result = self.elastic_search_api.get_index(index_name)
        self.assertEquals(404, result.status_code)

    def test_get_index_does_exists(self):
        index_name = 'test_index'
        self.elastic_search_api.setup_index(index_name=index_name)
        result = self.elastic_search_api.get_index(index_name)
        self.assertEquals(200, result.status_code)
        self.elastic_search_api.delete_index(index_name='test_index')

    def test_delete_index(self):
        index_name = 'test_index'
        response = self.elastic_search_api.setup_index(index_name=index_name)
        self.assertEquals(200, response.status_code)
        result = self.elastic_search_api.get_index(index_name)
        self.assertEquals(200, result.status_code)
        self.elastic_search_api.delete_index(index_name)
        result = self.elastic_search_api.get_index(index_name)
        self.assertEquals(404, result.status_code)

    def test_index_document(self):
        facility = mommy.make(Facility, name='Fig tree medical clinic')
        result = search_utils.index_instance(facility)
        self.assertEquals(201, result.status_code)

    def test_search_document_no_instance_type(self):
        index_name = 'test_index'
        response = self.elastic_search_api.setup_index(index_name=index_name)
        self.assertEquals(200, response.status_code)
        facility = mommy.make(Facility, name='Fig tree medical clinic')
        result = search_utils.index_instance(facility)
        self.assertEquals(201, result.status_code)
        self.elastic_search_api.search_document(
            index_name=index_name, instance_type='facility', query='tree')

    def test_remove_document(self):
        index_name = 'test_index'
        self.elastic_search_api.setup_index(index_name=index_name)
        facility = mommy.make(Facility, name='Fig tree medical clinic')
        result = search_utils.index_instance(facility)
        self.assertEquals(201, result.status_code)
        self.elastic_search_api.remove_document(
            index_name, 'facility', str(facility.id))
        self.elastic_search_api.delete_index(index_name='test_index')

    def test_update_document(self):
        pass

    def test_test_delete_document(self):
        pass


class TestSearchFunctions(ViewTestBase):
    def test_serialize_model(self):
        facility = mommy.make(Facility)
        serialized_data = FacilitySerializer(facility).data
        expected_data = FacilitySerializer(facility).data
        self.assertEquals(expected_data, serialized_data)

    def test_default_json_dumps_function(self):
        facility = mommy.make(Facility)
        data = FacilitySerializer(facility).data
        result = json.dumps(data, default=search_utils.default)
        self.assertIsInstance(result, str)

    def test_search_facility(self):
        url = reverse('api:facilities:facilities_list')
        facility = mommy.make(Facility, name='Kanyakini')
        search_utils.index_instance(facility)
        url = url + "?search={}".format('Kanyakini')
        response = self.client.get(url)
        self.assertEquals(200, response.status_code)
        expected_data = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                FacilitySerializer(facility).data
            ]
        }
        self._assert_response_data_equality(expected_data, response.data)


class TestSearchFilter(ViewTestBase):
    def test_filter(self):
        mommy.make(Facility, name='test facility')
        mommy.make(Facility)
        qs = Facility.objects.all()

        search_filter = SearchFilter(name='search', model=Facility)
        result = search_filter.filter(qs, 'test')
        # no documents have been indexed
        self.assertEquals(result, [])

import datetime
from decimal import Decimal

from django.test import TestCase

from experimenter.experiments.models import Experiment
from experimenter.experiments.tests.factories import (
    LocaleFactory,
    CountryFactory,
    ExperimentFactory,
    ExperimentVariantFactory,
)
from experimenter.experiments.serializers import (
    CountrySerializer,
    ExperimentRecipeAddonArgumentsSerializer,
    ExperimentRecipePrefArgumentsSerializer,
    ExperimentRecipeSerializer,
    ExperimentRecipeVariantSerializer,
    ExperimentSerializer,
    ExperimentVariantSerializer,
    FilterObjectBucketSampleSerializer,
    FilterObjectChannelSerializer,
    FilterObjectCountrySerializer,
    FilterObjectLocaleSerializer,
    JSTimestampField,
    LocaleSerializer,
    ExperimentCloneSerializer,
)

from experimenter.experiments.tests.mixins import MockRequestMixin


class TestJSTimestampField(TestCase):

    def test_field_serializes_to_js_time_format(self):
        field = JSTimestampField()
        example_datetime = datetime.datetime(2000, 1, 1, 1, 1, 1, 1)
        self.assertEqual(
            field.to_representation(example_datetime), 946688461000.0
        )

    def test_field_returns_none_if_no_datetime_passed_in(self):
        field = JSTimestampField()
        self.assertEqual(field.to_representation(None), None)


class TestExperimentVariantSerializer(TestCase):

    def test_serializer_outputs_expected_bool(self):
        experiment = ExperimentFactory(pref_type=Experiment.PREF_TYPE_BOOL)
        variant = ExperimentVariantFactory.create(
            experiment=experiment, value="true"
        )
        serializer = ExperimentRecipeVariantSerializer(variant)

        self.assertEqual(type(serializer.data["value"]), bool)
        self.assertEqual(
            serializer.data,
            {"ratio": variant.ratio, "slug": variant.slug, "value": True},
        )

    def test_serializer_outputs_expected_int_val(self):
        experiment = ExperimentFactory(pref_type=Experiment.PREF_TYPE_INT)
        variant = ExperimentVariantFactory.create(
            experiment=experiment, value="28"
        )
        serializer = ExperimentRecipeVariantSerializer(variant)

        self.assertEqual(type(serializer.data["value"]), int)
        self.assertEqual(
            serializer.data,
            {"ratio": variant.ratio, "slug": variant.slug, "value": 28},
        )

    def test_serializer_outputs_expected_str_val(self):
        experiment = ExperimentFactory(pref_type=Experiment.PREF_TYPE_STR)
        variant = ExperimentVariantFactory.create(experiment=experiment)
        serializer = ExperimentRecipeVariantSerializer(variant)

        self.assertEqual(type(serializer.data["value"]), str)
        self.assertEqual(
            serializer.data,
            {
                "ratio": variant.ratio,
                "slug": variant.slug,
                "value": variant.value,
            },
        )


class TestLocaleSerializer(TestCase):

    def test_serializer_outputs_expected_schema(self):
        locale = LocaleFactory.create()
        serializer = LocaleSerializer(locale)
        self.assertEqual(
            serializer.data, {"code": locale.code, "name": locale.name}
        )


class TestCountrySerializer(TestCase):

    def test_serializer_outputs_expected_schema(self):
        country = CountryFactory.create()
        serializer = CountrySerializer(country)
        self.assertEqual(
            serializer.data, {"code": country.code, "name": country.name}
        )


class TestExperimentSerializer(TestCase):

    def test_serializer_outputs_expected_schema(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_COMPLETE, countries=[], locales=[]
        )
        serializer = ExperimentSerializer(experiment)
        expected_data = {
            "analysis": experiment.analysis,
            "analysis_owner": experiment.analysis_owner,
            "client_matching": experiment.client_matching,
            "platform": experiment.platform,
            "end_date": JSTimestampField().to_representation(
                experiment.end_date
            ),
            "experiment_url": experiment.experiment_url,
            "firefox_channel": experiment.firefox_channel,
            "firefox_min_version": experiment.firefox_min_version,
            "firefox_max_version": experiment.firefox_max_version,
            "name": experiment.name,
            "objectives": experiment.objectives,
            "population": experiment.population,
            "population_percent": "{0:.4f}".format(
                experiment.population_percent
            ),
            "pref_branch": experiment.pref_branch,
            "pref_key": experiment.pref_key,
            "pref_type": experiment.pref_type,
            "addon_experiment_id": experiment.addon_experiment_id,
            "addon_release_url": experiment.addon_release_url,
            "proposed_start_date": JSTimestampField().to_representation(
                experiment.proposed_start_date
            ),
            "proposed_enrollment": experiment.proposed_enrollment,
            "proposed_duration": experiment.proposed_duration,
            "short_description": experiment.short_description,
            "slug": experiment.slug,
            "start_date": JSTimestampField().to_representation(
                experiment.start_date
            ),
            "type": experiment.type,
            "variants": [
                ExperimentVariantSerializer(variant).data
                for variant in experiment.variants.all()
            ],
            "locales": [],
            "countries": [],
        }

        self.assertEqual(
            set(serializer.data.keys()), set(expected_data.keys())
        )
        self.assertEqual(serializer.data, expected_data)

    def test_serializer_locales(self):
        locale = LocaleFactory()
        experiment = ExperimentFactory.create(locales=[locale])
        serializer = ExperimentSerializer(experiment)
        self.assertEqual(
            serializer.data["locales"],
            [{"code": locale.code, "name": locale.name}],
        )

    def test_serializer_countries(self):
        country = CountryFactory()
        experiment = ExperimentFactory.create(countries=[country])
        serializer = ExperimentSerializer(experiment)
        self.assertEqual(
            serializer.data["countries"],
            [{"code": country.code, "name": country.name}],
        )


class TestFilterObjectBucketSampleSerializer(TestCase):

    def test_serializer_outputs_expected_schema(self):
        experiment = ExperimentFactory.create(
            population_percent=Decimal("12.34")
        )
        serializer = FilterObjectBucketSampleSerializer(experiment)
        self.assertEqual(
            serializer.data,
            {
                "type": "bucketSample",
                "input": ["normandy.recipe.id", "normandy.userId"],
                "start": 0,
                "count": 1234,
                "total": 10000,
            },
        )


class TestFilterObjectChannelSerializer(TestCase):

    def test_serializer_outputs_expected_schema(self):
        experiment = ExperimentFactory.create(
            firefox_channel=Experiment.CHANNEL_NIGHTLY
        )
        serializer = FilterObjectChannelSerializer(experiment)
        self.assertEqual(
            serializer.data, {"type": "channel", "channels": ["nightly"]}
        )


class TestFilterObjectLocaleSerializer(TestCase):

    def test_serializer_outputs_expected_schema(self):
        locale1 = LocaleFactory.create(code="ab")
        locale2 = LocaleFactory.create(code="cd")
        experiment = ExperimentFactory.create(locales=[locale1, locale2])
        serializer = FilterObjectLocaleSerializer(experiment)
        self.assertEqual(serializer.data["type"], "locale")
        self.assertEqual(set(serializer.data["locales"]), set(["ab", "cd"]))


class TestFilterObjectCountrySerializer(TestCase):

    def test_serializer_outputs_expected_schema(self):
        country1 = CountryFactory.create(code="ab")
        country2 = CountryFactory.create(code="cd")
        experiment = ExperimentFactory.create(countries=[country1, country2])
        serializer = FilterObjectCountrySerializer(experiment)
        self.assertEqual(serializer.data["type"], "country")
        self.assertEqual(set(serializer.data["countries"]), set(["ab", "cd"]))


class TestExperimentRecipeVariantSerializer(TestCase):

    def test_serializer_outputs_expected_schema(self):
        experiment = ExperimentFactory(pref_type=Experiment.PREF_TYPE_STR)
        variant = ExperimentVariantFactory.create(experiment=experiment)
        serializer = ExperimentRecipeVariantSerializer(variant)
        self.assertEqual(
            serializer.data,
            {
                "ratio": variant.ratio,
                "slug": variant.slug,
                "value": variant.value,
            },
        )


class TestExperimentRecipePrefArgumentsSerializer(TestCase):

    def test_serializer_outputs_expected_schema(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_SHIP
        )
        serializer = ExperimentRecipePrefArgumentsSerializer(experiment)
        self.assertEqual(
            serializer.data,
            {
                "preferenceBranchType": experiment.pref_branch,
                "slug": experiment.normandy_slug,
                "experimentDocumentUrl": experiment.experiment_url,
                "preferenceName": experiment.pref_key,
                "preferenceType": experiment.pref_type,
                "branches": [
                    ExperimentRecipeVariantSerializer(variant).data
                    for variant in experiment.variants.all()
                ],
            },
        )


class TestExperimentRecipeAddonArgumentsSerializer(TestCase):

    def test_serializer_outputs_expected_schema(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_SHIP
        )
        serializer = ExperimentRecipeAddonArgumentsSerializer(experiment)
        self.assertEqual(
            serializer.data,
            {
                "name": experiment.addon_experiment_id,
                "description": experiment.public_description,
            },
        )


class TestExperimentRecipeSerializer(TestCase):

    def test_serializer_outputs_expected_schema_for_pref_experiment(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_SHIP,
            type=Experiment.TYPE_PREF,
            locales=[LocaleFactory.create()],
            countries=[CountryFactory.create()],
        )
        serializer = ExperimentRecipeSerializer(experiment)
        self.assertEqual(
            serializer.data["action_name"], "preference-experiment"
        )
        self.assertEqual(serializer.data["name"], experiment.name)
        self.assertEqual(
            serializer.data["comment"], experiment.client_matching
        )
        self.assertEqual(
            serializer.data["filter_object"],
            [
                FilterObjectBucketSampleSerializer(experiment).data,
                FilterObjectChannelSerializer(experiment).data,
                FilterObjectLocaleSerializer(experiment).data,
                FilterObjectCountrySerializer(experiment).data,
            ],
        )
        self.assertEqual(
            serializer.data["arguments"],
            ExperimentRecipePrefArgumentsSerializer(experiment).data,
        )

    def test_serializer_outputs_expected_schema_for_addon_experiment(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_SHIP,
            type=Experiment.TYPE_ADDON,
            locales=[LocaleFactory.create()],
            countries=[CountryFactory.create()],
        )
        serializer = ExperimentRecipeSerializer(experiment)
        self.assertEqual(serializer.data["action_name"], "opt-out-study")
        self.assertEqual(serializer.data["name"], experiment.name)
        self.assertEqual(
            serializer.data["comment"], experiment.client_matching
        )
        self.assertEqual(
            serializer.data["filter_object"],
            [
                FilterObjectBucketSampleSerializer(experiment).data,
                FilterObjectChannelSerializer(experiment).data,
                FilterObjectLocaleSerializer(experiment).data,
                FilterObjectCountrySerializer(experiment).data,
            ],
        )
        self.assertEqual(
            serializer.data["arguments"],
            ExperimentRecipeAddonArgumentsSerializer(experiment).data,
        )

    def test_serializer_excludes_locales_if_none_set(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_SHIP, type=Experiment.TYPE_ADDON
        )
        experiment.locales.all().delete()
        serializer = ExperimentRecipeSerializer(experiment)
        filter_object_types = [
            f["type"] for f in serializer.data["filter_object"]
        ]
        self.assertNotIn("locale", filter_object_types)

    def test_serializer_excludes_countries_if_none_set(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_SHIP, type=Experiment.TYPE_ADDON
        )
        experiment.countries.all().delete()
        serializer = ExperimentRecipeSerializer(experiment)
        filter_object_types = [
            f["type"] for f in serializer.data["filter_object"]
        ]
        self.assertNotIn("country", filter_object_types)


class TestCloneSerializer(MockRequestMixin, TestCase):

    def test_clone_serializer_rejects_duplicate_slug(self):
        experiment_1 = ExperimentFactory.create(
            name="good experiment", slug="great-experiment"
        )
        clone_data = {"name": "great experiment"}
        serializer = ExperimentCloneSerializer(
            instance=experiment_1, data=clone_data
        )

        self.assertFalse(serializer.is_valid())

    def test_clone_serializer_rejects_duplicate_name(self):
        experiment = ExperimentFactory.create(
            name="wonderful experiment", slug="amazing-experiment"
        )
        clone_data = {"name": "wonderful experiment"}
        serializer = ExperimentCloneSerializer(
            instance=experiment, data=clone_data
        )

        self.assertFalse(serializer.is_valid())

    def test_clone_serializer_rejects_invalid_name(self):
        experiment = ExperimentFactory.create(
            name="great experiment", slug="great-experiment"
        )

        clone_data = {"name": "@@@@@@@@"}
        serializer = ExperimentCloneSerializer(
            instance=experiment, data=clone_data
        )

        self.assertFalse(serializer.is_valid())

    def test_clone_serializer_accepts_unique_name(self):
        experiment = ExperimentFactory.create(
            name="great experiment", slug="great-experiment"
        )
        clone_data = {"name": "best experiment"}
        serializer = ExperimentCloneSerializer(
            instance=experiment,
            data=clone_data,
            context={"request": self.request},
        )
        self.assertTrue(serializer.is_valid())

        serializer.save()

        self.assertEqual(serializer.data["name"], "best experiment")
        self.assertEqual(
            serializer.data["clone_url"], "/experiments/best-experiment/"
        )

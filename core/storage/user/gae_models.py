# coding: utf-8
#
# Copyright 2014 The Oppia Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Models for Oppia users."""

__author__ = 'Stephanie Federwisch'

from core.platform import models
(base_models,) = models.Registry.import_models([models.NAMES.base_model])
import feconf

from google.appengine.ext import ndb


class UserSettingsModel(base_models.BaseModel):
    """Settings and preferences for a particular user.

    Instances of this class are keyed by the user id.
    """
    # Email address of the user.
    email = ndb.StringProperty(required=True, indexed=True)

    # Identifiable username to display in the UI. May be None.
    username = ndb.StringProperty(indexed=True)
    # Normalized username to use for duplicate-username queries. May be None.
    normalized_username = ndb.StringProperty(indexed=True)
    # When the user last agreed to the terms of the site. May be None.
    last_agreed_to_terms = ndb.DateTimeProperty(default=None)
    # When the user last started the state editor tutorial. May be None.
    last_started_state_editor_tutorial = ndb.DateTimeProperty(default=None)
    # User uploaded profile picture as a dataURI string. May be None.
    profile_picture_data_url = ndb.TextProperty(default=None, indexed=False)
    # User specified biography (to be shown on their profile page).
    user_bio = ndb.TextProperty(indexed=False)
    # The time, in milliseconds, when the user first contributed to Oppia.
    # May be None.
    first_contribution_msec = ndb.FloatProperty(default=None)
    # Language preferences specified by the user.
    # TODO(sll): Add another field for the language that the user wants the
    # site to display in. These language preferences are mainly for the purpose
    # of figuring out what to show by default in the gallery.
    preferred_language_codes = ndb.StringProperty(repeated=True, indexed=True,
        choices=[lc['code'] for lc in feconf.ALL_LANGUAGE_CODES])

    @classmethod
    def is_normalized_username_taken(cls, normalized_username):
        """Returns whether or a given normalized_username is taken."""
        return bool(cls.get_all().filter(
            cls.normalized_username == normalized_username).get())

    @classmethod
    def get_by_normalized_username(cls, normalized_username):
        """Returns a user model given a normalized username"""
        return cls.get_all().filter(
            cls.normalized_username == normalized_username).get()


class UserEmailPreferencesModel(base_models.BaseModel):
    """Email preferences for a particular user.

    Instances of this class are keyed by the user id.
    """
    # The user's preference for receiving general site updates. This is set to
    # None if the user has never set a preference.
    site_updates = ndb.BooleanProperty(indexed=True)


class UserSubscriptionsModel(base_models.BaseModel):
    """A list of things that a user subscribes to.

    Instances of this class are keyed by the user id.
    """
    # IDs of activities (e.g., explorations) that this user subscribes to.
    # TODO(bhenning): Rename this to exploration_ids and perform a migration.
    activity_ids = ndb.StringProperty(repeated=True, indexed=True)
    # IDs of collections that this user subscribes to.
    collection_ids = ndb.StringProperty(repeated=True, indexed=True)
    # IDs of feedback thread ids that this user subscribes to.
    feedback_thread_ids = ndb.StringProperty(repeated=True, indexed=True)
    # When the user last checked notifications. May be None.
    last_checked = ndb.DateTimeProperty(default=None)


class UserRecentChangesBatchModel(base_models.BaseMapReduceBatchResultsModel):
    """A list of recent changes corresponding to things a user subscribes to.

    This is computed using a MapReduce batch job and may not be up to date.
    Instances of this class are keyed by the user id.
    """
    # The output of the batch job.
    output = ndb.JsonProperty(indexed=False)
    # The time, in milliseconds since the epoch, when the job that computed
    # this batch model was queued.
    job_queued_msec = ndb.FloatProperty(indexed=False)


class ExplorationUserDataModel(base_models.BaseModel):
    """User-specific data pertaining to a specific exploration.

    Instances of this class have keys of the form
    [USER_ID].[EXPLORATION_ID]
    """

    # The user id.
    user_id = ndb.StringProperty(required=True, indexed=True)
    # The exploration id.
    exploration_id = ndb.StringProperty(required=True, indexed=True)

    # The rating (1-5) the user assigned to the exploration. Note that this
    # represents a rating given on completion of the exploration.
    rating = ndb.IntegerProperty(default=None, indexed=True)

    # When the most recent rating was awarded, or None if not rated.
    rated_on = ndb.DateTimeProperty(default=None, indexed=False)

    @classmethod
    def _generate_id(cls, user_id, exploration_id):
        return '%s.%s' % (user_id, exploration_id)

    @classmethod
    def create(cls, user_id, exploration_id):
        """Creates a new ExplorationUserDataModel entry and returns it.

        Note that the client is responsible for actually saving this entity to
        the datastore.
        """
        instance_id = cls._generate_id(user_id, exploration_id)
        return cls(
            id=instance_id, user_id=user_id, exploration_id=exploration_id)

    @classmethod
    def get(cls, user_id, exploration_id):
        """Gets the ExplorationUserDataModel for the given ids."""
        instance_id = cls._generate_id(user_id, exploration_id)
        return super(ExplorationUserDataModel, cls).get(
            instance_id, strict=False)


class CollectionProgressModel(base_models.BaseModel):
    """Stores progress a user has made within a collection, including all
    explorations which have been completed within the context of the collection.

    Please note instances of this progress model will persist even after a
    collection is deleted.

    TODO(bhenning): Implement a job which removes stale versions of this model
    in the data store. That is, it should go through all completion models and
    ensure both the user and collection it is associated with still exist within
    the data store, otherwise it should remove the instance of the completion
    model.
    """

    # The user id.
    user_id = ndb.StringProperty(required=True, indexed=True)
    # The collection id.
    collection_id = ndb.StringProperty(required=True, indexed=True)
    # The list of explorations which have been completed within the context of
    # the collection represented by collection_id.
    completed_explorations = ndb.StringProperty(repeated=True)

    @classmethod
    def _generate_id(cls, user_id, collection_id):
        return '%s.%s' % (user_id, collection_id)

    @classmethod
    def create(cls, user_id, collection_id):
        """Creates a new CollectionProgressModel entry and returns it.

        Note: the client is responsible for actually saving this entity to the
        datastore.
        """
        instance_id = cls._generate_id(user_id, collection_id)
        return cls(
            id=instance_id, user_id=user_id, collection_id=collection_id)

    @classmethod
    def get(cls, user_id, collection_id):
        """Gets the CollectionProgressModel for the given ids."""

        instance_id = cls._generate_id(user_id, collection_id)
        return super(CollectionProgressModel, cls).get(
            instance_id, strict=False)

    @classmethod
    def get_or_create(cls, user_id, collection_id):
        """Gets the CollectionProgressModel for the given ids, or creates a new
        entry with the given ids if no such instance yet exists within the data
        store.
        """
        instance_model = cls.get(user_id, collection_id)
        if instance_model:
            return instance_model
        else:
            return cls.create(user_id, collection_id)

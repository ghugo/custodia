# Copyright 2017 AT&T
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os

from custodia.plugin import CSStore, CSStoreError, CSStoreExists

from barbicanclient import client
from keystoneauth1 import identity
from keystoneauth1 import session

# TODO(gagehugo): Get this from the keystone endpoint instead
BARBICAN_URL = 'http://controller:9311/v1/{}/{}'

class BarbicanStore(CSStore):

    def __init__(self, config, section):
        super(BarbicanStore, self).__init__(config, section)
        self.session = None

    def _create_barbican_session(self):
        return client.Client(session=self.session)

    def _get_container(self, barbican, ref):
        href = BARBICAN_URL.format('containers', ref)
        try:
            container = barbican.containers.get(href)
        except:
            self.logger.exception("Error fetching container %s", href)
            raise CSStoreError('Error occurred while trying to get container')

        return container

    def _get_secret(self, barbican, ref):
        try:
            secret = barbican.secrets.get(ref)
        except:
            self.logger.exception('Error fetching key %s', href)
            raise CSStoreError('Error occurred while trying to get secret')

        return secret

    def get(self, key):
        sess = self._create_barbican_session()
        key_name = key.split('/')[-1]
        container_ref = key.split('/')[-2]

        container = self._get_container(sess, container_ref)

        for name, ref in container.secret_refs.items():
            if name == key_name:
                secret = self._get_secret(sess, ref)
                return secret.payload

        return None

    def set(self, key, value, replace=False):
        self.logger.debug('Setting key %s to value %s (replace=%s)',
                          key, value, replace)
        if key.endswith('/'):
            raise ValueError('Invalid key name, cannot end in "/"')
        container_ref = key.split('/')[-2]
        keyid = key.split('/')[-1]

        sess = self._create_barbican_session()
        secret = sess.secrets.create(name=keyid,payload=value)
        secret_ref = secret.store()

        json_body = {
            'name': keyid,
            'secret_ref': secret_ref
        }
        url = BARBICAN_URL.format('containers', container_ref) + '/secrets'
        response = self.session.post(url, json=json_body)
        return response.json()['container_ref']

        #container = self._get_container(sess, container_ref)
        #container.secret_refs[keyid] = secret.secret_ref
        #container.add(keyid, secret)
        #return str(container.store())

    def span(self, key):
        barbican = self._create_barbican_session()
        name = key.rsplit('/')[-2]
        self.logger.debug('Creating container %s', name)
        container = barbican.containers.create(name=name)
        return str(container.store())

    def list(self, keyfilter=''):
        path = keyfilter.rstrip('/')
        self.logger.debug('Listing keys matching %s', path)
        child_prefix = path if path == '' else path + '/'

        barbican = self._create_barbican_session()
        values = barbican.secrets.list()
        secrets = []

        for value in values:
            secrets.append(value.secret_ref)

        return secrets

    def cut(self, key):
        barbican = self._create_barbican_session()
        name = key.rstrip('/')
        self.logger.debug('Removing container %s', name)
        barbican.containers.remove(name)

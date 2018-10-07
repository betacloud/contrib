#!/usr/bin/env python

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging
import sys

from oslo_config import cfg
import openstack

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')

PROJECT_NAME = 'glance-share-image'
CONF = cfg.CONF
opts = [
    cfg.StrOpt('action', required=False, help='Action', default='add'),
    cfg.StrOpt('cloud', required=False, help='Managed cloud', default='service'),
    cfg.StrOpt('project-domain', required=False, help='Target project domain', default='default'),
    cfg.StrOpt('image', required=True, help='Image to share'),
    cfg.StrOpt('target', required=True, help='Target project or domain'),
    cfg.StrOpt('type', required=True, help='Project or domain', default='project')
]
CONF.register_cli_opts(opts)

def unshare_image_with_project(conn, image, project):
    member = conn.image.find_member(project.id, image.id)

    if member:
        logging.info("del - %s - %s (%s)" % (image.name, project.name, project.domain_id))
        conn.image.remove_member(member, image.id)

def share_image_with_project(conn, image, project):
    member = conn.image.find_member(project.id, image.id)

    if not member:
        logging.info("add - %s - %s (%s)" % (image.name, project.name, project.domain_id))
        member = conn.image.add_member(image.id, member_id=project.id)

    if member.status != "accepted":
        conn.image.update_member(member, image.id, status="accepted")

if __name__ == '__main__':
    CONF(sys.argv[1:], project=PROJECT_NAME)

    conn = openstack.connect(cloud=CONF.cloud)

    image = conn.get_image(CONF.image)

    if CONF.type == "project":
        domain = conn.get_domain(name_or_id=CONF.project_domain)
        project = conn.get_project(CONF.target, domain_id=domain.id)

        if CONF.action == "add":
            share_image_with_project(conn, image, project)
        elif CONF.action == "del":
            unshare_image_with_project(conn, image, project)

    elif CONF.type == "domain":
        domain = conn.get_domain(name_or_id=CONF.target)
        projects = conn.list_projects(domain_id=domain.id)
        for project in projects:
            if CONF.action == "add":
                share_image_with_project(conn, image, project)
            elif CONF.action == "del":
                unshare_image_with_project(conn, image, project)

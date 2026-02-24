# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM nginx:alpine

# The nginx:alpine image automatically runs envsubst on files in templates/
# This allows us to inject PORT, API_URL, and ADMIN_API_KEY dynamically at runtime.
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# Copy the static web application files into Nginx's serving directory
COPY static /usr/share/nginx/html

# Expose the default Cloud Run port
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]

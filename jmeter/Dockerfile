#
# Copyright 2020, Fernando Lemes da Silva
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

FROM alpine:3.10

MAINTAINER Fernando Lemes da Silva <lemes@ime.usp.br>

ARG JMETER_VERSION="5.1.1"
ENV JMETER_HOME /opt/apache-jmeter-${JMETER_VERSION}
ENV JMETER_BIN ${JMETER_HOME}/bin
ENV JMETER_DOWNLOAD_URL https://archive.apache.org/dist/jmeter/binaries/apache-jmeter-${JMETER_VERSION}.tgz

RUN apk update && \
	apk upgrade && \
	apk add ca-certificates && \
	update-ca-certificates && \
	apk add --update openjdk8-jre tzdata curl unzip bash && \
	apk add --no-cache nss && \
	rm -rf /var/cache/apk/* && \
	mkdir -p /tmp/dependencies  && \
	curl -L --silent ${JMETER_DOWNLOAD_URL} > /tmp/dependencies/apache-jmeter-${JMETER_VERSION}.tgz && \
	mkdir -p /opt && \
	tar -xzf /tmp/dependencies/apache-jmeter-${JMETER_VERSION}.tgz -C /opt  && \
	rm -rf /tmp/dependencies && \
	mkdir /tests && \
	mkdir /results

ENV PATH $PATH:$JMETER_BIN

COPY jmeter/run.sh /run.sh
COPY jmeter/test_1.jmx /tests/test_1.jmx

VOLUME /results

ENTRYPOINT ["/run.sh"]

#!/bin/bash
set +x # show commands
set -e # fail on first error
VERSION=1
HELM_USERNAME=crosslang
HELM_PASSWORD=isthebest
if [ ! -z "$BUILD_ID" ]; then
  VERSION=$BUILD_ID
fi
if [ -d "helm" ]; then
  rm -R helm
fi
mkdir helm
cd helm
echo $PWD
docker run --user $(id -u):$(id -g) \
  -v $PWD:/src \
  -v $PWD/../docker-kompose.yaml:/src/docker-compose.yaml \
  -v $PWD/../secrets:/src/secrets \
  --rm femtopixel/kompose convert -o fisma-ctlg-manager -c
cd fisma-ctlg-manager
# work around: https://github.com/kubernetes/kompose/issues/1096
patch -p0 templates/postgres-deployment.yaml ../../postgres-deployment.yaml.patch
# work around: Cannot write to /var/solr as 8983:8983
patch -p0 templates/solr-deployment.yaml ../../solr-deployment.yaml.patch
docker run --user $(id -u):$(id -g) -v $PWD:/fisma-ctlg-manager -v $PWD:/apps --rm alpine/helm:latest package /fisma-ctlg-manager --version $VERSION
curl -u $HELM_USERNAME:$HELM_PASSWORD https://nexus.crosslang.com/repository/helm-repo/ --upload-file fisma-ctlg-manager-$VERSION.tgz

VERSION=1.0.0
HELM_USERNAME=crosslang
HELM_PASSWORD=***REMOVED***
if [ ! -z "$BUILD_ID" ]; then
  VERSION=$BUILD_ID
fi
if [ -d "helm/fisma-ctlg-manager" ]; then
  rm -R helm/fisma-ctlg-manager
fi
mkdir -p helm
docker run -v $PWD:/src -v $PWD/../docker-kompose.yml:/src/docker-compose.yaml -v $PWD/../secrets/django-docker.env:/src/secrets/django-docker.env --rm -it femtopixel/kompose convert -o fisma-ctlg-manager -c
cd fisma-ctlg-manager
docker run -v $PWD:/fisma-ctlg-manager -v $PWD:/apps -it --rm alpine/helm:latest package /fisma-ctlg-manager --version $VERSION
curl -u $HELM_USERNAME:$HELM_PASSWORD https://nexus.crosslang.com/repository/helm-repo/ --upload-file fisma-ctlg-manager-$VERSION.tgz -v

#Build docker images


echo
echo "BUILD STARTED"
echo

if [ -z "${TAG_BDC_COLLECTION_BUILDER}" ]; then
  echo "NEW TAG BDC-COLLECTION-BUILDER:"
  read TAG_BDC_COLLECTION_BUILDER

  echo
fi

export IMAGE_BDC_COLLECTION_BUILDER="registry.dpi.inpe.br/brazildatacube/bdc-collection-builder"
export IMAGE_BDC_COLLECTION_BUILDER_FULL="${IMAGE_BDC_COLLECTION_BUILDER}:${TAG_BDC_COLLECTION_BUILDER}"
echo "IMAGE BDC COLLECTION-BUILDER :: ${IMAGE_BDC_COLLECTION_BUILDER_FULL}"

docker-compose build
docker tag ${IMAGE_BDC_COLLECTION_BUILDER}:latest ${IMAGE_BDC_COLLECTION_BUILDER_FULL}
docker push ${IMAGE_BDC_COLLECTION_BUILDER_FULL}

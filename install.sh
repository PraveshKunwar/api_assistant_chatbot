oc new-build \
    --name=um-api-assistant \
    --strategy=docker \
    --binary \
    -l app.kubernetes.io/part-of=STREAMLIT-APPS \
    -l app=um-api-assistant

oc start-build \
    um-api-assistant \
    --from-dir=. \
    --follow

oc new-app \
    um-api-assistant \
    -l app.kubernetes.io/part-of=STREAMLIT-APPS \
    -l app=um-api-assistant

oc create -f route.yaml

oc set env deployment/um-api-assistant \
    --from=secret/maizey-secret
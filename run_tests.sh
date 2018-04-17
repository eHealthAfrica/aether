kubectl exec -it $(kubectl get pods | grep kernel | awk '{print $1}') --container kernel -- bash /code/entrypoint.sh test_coverage

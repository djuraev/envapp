# envapp — Kubernetes ConfigMap & Secret Lab

A minimal Python app (zero dependencies, pure stdlib) that displays
its environment variables in the browser. Used to teach ConfigMap and Secret.

---

## Project structure

```
envapp/
├── server.py          ← the app (pure Python, no pip install needed)
├── Dockerfile
└── k8s/
    ├── configmap.yaml
    ├── secret.yaml
    └── deployment.yaml
```

---

## Step 0 — Start minikube

```bash
minikube start --driver=docker
```

---

## Step 1 — Build the image inside minikube

```bash
# point your terminal's Docker CLI at minikube's daemon
eval $(minikube docker-env)

# build the image
docker build -t envapp:1.0 .

# confirm it's there
docker images | grep envapp
```

---

## Step 2 — Deploy (no config yet)

```bash
kubectl create deployment envapp \
  --image=envapp:1.0 \
  --port=8080

kubectl patch deployment envapp --type='json' \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/imagePullPolicy","value":"Never"}]'

kubectl get pods -w     # wait until Running
```

```bash
kubectl port-forward deployment/envapp 8080:8080
```

Open http://localhost:8080
→ Header shows "unknown", table says "No APP_ variables found"

---

## Step 3 — Apply ConfigMap

```bash
kubectl apply -f k8s/configmap.yaml
kubectl describe configmap app-config     # inspect the values
```

Inject it into the deployment:

```bash
kubectl set env deployment/envapp --from=configmap/app-config
kubectl rollout status deployment/envapp
```

```bash
kubectl port-forward deployment/envapp 8080:8080
```

Refresh http://localhost:8080
→ Header turns RED (production), table shows all 7 keys

---

## Step 4 — Change a value WITHOUT touching the Deployment

```bash
kubectl edit configmap app-config
# change APP_ENV from production → staging
# change APP_COLOR from blue → green
```

```bash
kubectl rollout restart deployment/envapp
kubectl port-forward deployment/envapp 8080:8080
```

Refresh browser → header turns ORANGE (staging), APP_COLOR is green

---

## Step 5 — Apply Secret

```bash
kubectl apply -f k8s/secret.yaml
kubectl describe secret app-secret       # values show as <hidden>
```

```bash
kubectl set env deployment/envapp --from=secret/app-secret
kubectl rollout restart deployment/envapp
kubectl port-forward deployment/envapp 8080:8080
```

Refresh → DB_PASSWORD and API_KEY now appear in the table

---

## Step 6 — Full deployment (everything together)

```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml    # includes NodePort service

kubectl get pods
kubectl get svc
```

Access via NodePort (no port-forward needed):

```bash
minikube service envapp
# → opens browser at http://192.168.49.2:30080
```

---

## Debugging commands

```bash
# check what env vars the pod actually has
kubectl exec deployment/envapp -- env | grep -E "APP_|DB_|API_|FEATURE_"

# inspect configmap
kubectl get configmap app-config -o yaml

# inspect secret (base64 encoded)
kubectl get secret app-secret -o yaml

# decode a secret value manually
echo "c3VwZXJzZWNyZXQxMjM=" | base64 -d

# why is the pod not starting?
kubectl describe pod <pod-name>     # check Events section

# watch rollout
kubectl rollout status deployment/envapp
kubectl rollout history deployment/envapp
```

---

## Colour coding (for teaching)

| APP_ENV value  | Header colour |
|----------------|---------------|
| production     | Red           |
| staging        | Orange        |
| dev            | Green         |
| anything else  | Blue          |

Change APP_ENV in the ConfigMap and restart — students see the colour change live.

---

## Header bar colours per environment

| Env        | Color  | Hex     |
|------------|--------|---------|
| production | red    | #dc2626 |
| staging    | orange | #d97706 |
| dev        | green  | #16a34a |
| other      | blue   | #3b82f6 |

---

## Cleanup

```bash
kubectl delete deployment envapp
kubectl delete svc envapp
kubectl delete configmap app-config
kubectl delete secret app-secret
minikube stop
```

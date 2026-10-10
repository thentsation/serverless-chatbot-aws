FROM public.ecr.aws/lambda/python:3.14

# Patch OS CVEs from the base image and drop the local-only Runtime Interface
# Emulator (a Go binary with unfixed stdlib CVEs; not used inside AWS Lambda).
RUN dnf upgrade -y --releasever=latest && dnf clean all && rm -rf /var/cache/dnf \
    && rm -f /usr/local/bin/aws-lambda-rie

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY app.py ./

CMD ["app.handler"]

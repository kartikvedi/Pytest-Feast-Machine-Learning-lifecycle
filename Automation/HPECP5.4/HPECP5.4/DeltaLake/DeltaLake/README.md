<div class="cell markdown" data-tags="[]">

# Prerequistes :

</div>

<div class="cell markdown" data-tags="[]">

*1- Create a bucket in MinIO <b>deltalake-spark</b>.*<br> *2- Create
a directory <b>code</b> in bucket <b>deltalake-spark</b> and upload
<b>loans-delta-lake-demo.py</b> file in it.*<br> *3- Create directory
<b>data</b> in bucket <b>deltalake-spark</b> and upload
<b>SAISEU19-loan-risks.snappy.parquet</b> file in it.*<br><br><br> ![alt
text](images/MinIO.PNG)

</div>

<div class="cell markdown" data-tags="[]">

### Load the Kubeconfig

</div>

<div class="cell code">

``` python
%kubeRefresh --pwd Admin123
```

</div>

<div class="cell markdown" data-tags="[]">

# If MinIO is running on Self Signed Certificate.

Note: Please update MinIO endpoint, creditials and service account name
as per your environment.

</div>

<div class="cell markdown" data-tags="[]">

### Submit Spark Job

</div>

<div class="cell code">

``` python
!kubectl create -f deltalake-spark312-SSL.yaml
```

</div>

<div class="cell markdown" data-tags="[]">

### Check Spark job logs.

</div>

<div class="cell code">

``` python
!kubectl logs deltalake-spark312-ssl-driver  
```

</div>

<div class="cell markdown" data-tags="[]">

### Clean up

</div>

<div class="cell code">

``` python
!kubectl delete -f deltalake-spark312-SSL.yaml
```

</div>

<div class="cell markdown" data-tags="[]">

# If MinIO is not running on SSL.

Note: Please update MinIO endpoint, creditials and service account name
as per your environment.

</div>

<div class="cell markdown" data-tags="[]">

### Submit Spark Job

</div>

<div class="cell code">

``` python
!kubectl create -f deltalake-spark312-noSSL.yaml
```

</div>

<div class="cell markdown" data-tags="[]">

### Check Spark job logs.

</div>

<div class="cell code">

``` python
!kubectl logs deltalake-spark312-nossl-driver
```

</div>

<div class="cell markdown" data-tags="[]">

### Clean up

</div>

<div class="cell code">

``` python
!kubectl delete -f deltalake-spark312-noSSL.yaml
```

</div>

<div class="cell markdown" data-tags="[]">

## We can also submit these spark jobs from web terminal.

</div>

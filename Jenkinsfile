#!groovy

pipeline {
    environment {
        VERSION = ''
        HELM_USERNAME='crosslang'
        HELM_PASSWORD='isthebest'
    }

    agent { label 'master' }

    stages {
        stage('Build Docker images') {
            steps {
                dir('django'){
                    script {
                        docker.withRegistry("https://docker.crosslang.com", "docker-crosslang-com") {
                            def customImage = docker.build("ctlg-manager/django:${env.BUILD_ID}", "-f Dockerfile.prod .")
                            customImage.push()
                        }
                    }
                }
                dir('angular'){
                    script {
                        docker.withRegistry("https://docker.crosslang.com", "docker-crosslang-com") {
                            def customImage = docker.build("ctlg-manager/angular:${env.BUILD_ID}", "-f Dockerfile .")
                            customImage.push()
                        }
                    }
                }
                dir('scrapy'){
                    script {
                        docker.withRegistry("https://docker.crosslang.com", "docker-crosslang-com") {
                            def customImage = docker.build("ctlg-manager/scrapyd:${env.BUILD_ID}", "-f Dockerfile .")
                            customImage.push()
                        }
                    }
                }
                dir('solr'){
                    script {
                        docker.withRegistry("https://docker.crosslang.com", "docker-crosslang-com") {
                            def customImage = docker.build("ctlg-manager/solr:${env.BUILD_ID}", "-f Dockerfile .")
                            customImage.push()
                        }
                    }
                }
            }
        }
        stage('Deploy Helm Chart') {
            steps {
                //sh 'rm -R helm/fisma-ctlg-manager'
                sh 'cd helm'
                sh 'docker run -v $PWD:/src -v $PWD/../docker-kompose.yml:/src/docker-compose.yaml -v $PWD/../secrets/django-docker.env:/src/secrets/django-docker.env --rm -it femtopixel/kompose convert -o fisma-ctlg-manager -c'
                sh 'cd fisma-ctlg-manager'
                sh 'docker run -v $PWD:/fisma-ctlg-manager -v $PWD:/apps -it --rm alpine/helm:latest package /fisma-ctlg-manager --version $BUILD_ID'
                sh 'curl -u $HELM_USERNAME:$HELM_PASSWORD https://nexus.crosslang.com/repository/helm-repo/ --upload-file fisma-ctlg-manager-$BUILD_ID.tgz -v'
            }
        }
    }

    post {
        success {
            //slackSend (color: '#36A64F', message: "SUCCESSFUL: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})")
        }
        failure {
            //slackSend (color: '#FF0000', message: "FAILED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})")
        }
    }
}


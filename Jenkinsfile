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
                            customImage.push("latest")
                        }
                    }
                }
                dir('angular'){
                    script {
                        docker.withRegistry("https://docker.crosslang.com", "docker-crosslang-com") {
                            def customImage = docker.build("ctlg-manager/angular:${env.BUILD_ID}", "-f Dockerfile .")
                            customImage.push()
                            customImage.push("latest")
                        }
                    }
                }
                dir('scrapy'){
                    script {
                        docker.withRegistry("https://docker.crosslang.com", "docker-crosslang-com") {
                            def customImage = docker.build("ctlg-manager/scrapyd:${env.BUILD_ID}", "-f Dockerfile .")
                            customImage.push()
                            customImage.push("latest")
                        }
                    }
                }
                dir('solr'){
                    script {
                        docker.withRegistry("https://docker.crosslang.com", "docker-crosslang-com") {
                            def customImage = docker.build("ctlg-manager/solr:${env.BUILD_ID}", "-f Dockerfile .")
                            customImage.push()
                            customImage.push("latest")
                        }
                    }
                }
            }
        }
        stage('Deploy Helm Chart') {
            steps {
                sh './kompose.sh'
            }
        }
    }

/*
    post {
        success {
            slackSend (color: '#36A64F', message: "SUCCESSFUL: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})")
        }
        failure {
            slackSend (color: '#FF0000', message: "FAILED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})")
        }
    }
    */
}


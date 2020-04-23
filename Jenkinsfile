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
                            def customImage = docker.build("ctlg-manager/django:${env.BRANCH_NAME}-${env.BUILD_ID}", "-f Dockerfile.prod .")
                            customImage.push()
                            customImage.push("${env.BRANCH_NAME}-latest")
                        }
                    }
                }
                dir('angular'){
                    script {
                        docker.withRegistry("https://docker.crosslang.com", "docker-crosslang-com") {
                            def customImage = docker.build("ctlg-manager/angular:${env.BRANCH_NAME}-${env.BUILD_ID}", "-f Dockerfile .")
                            customImage.push()
                            customImage.push("${env.BRANCH_NAME}-latest")
                        }
                    }
                }
                dir('scrapy'){
                    script {
                        docker.withRegistry("https://docker.crosslang.com", "docker-crosslang-com") {
                            def customImage = docker.build("ctlg-manager/scrapyd:${env.BRANCH_NAME}-${env.BUILD_ID}", "-f Dockerfile .")
                            customImage.push()
                            customImage.push("${env.BRANCH_NAME}-latest")
                        }
                    }
                }
                dir('solr'){
                    script {
                        docker.withRegistry("https://docker.crosslang.com", "docker-crosslang-com") {
                            def customImage = docker.build("ctlg-manager/solr:${env.BRANCH_NAME}-${env.BUILD_ID}", "-f Dockerfile .")
                            customImage.push()
                            customImage.push("${env.BRANCH_NAME}-latest")
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


#!groovy
pipeline {
    tools {
        maven 'maven 3.3.9'
        jdk 'Java 1.8'
    }
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
                dir('django/nginx'){
                    script {
                        docker.withRegistry("https://docker.crosslang.com", "docker-crosslang-com") {
                            def customImage = docker.build("ctlg-manager/django_nginx:${env.BRANCH_NAME}-${env.BUILD_ID}", "-f Dockerfile .")
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
            }
        }
        stage('Download git submodules: uima') {
            steps {
                sh "git submodule update --init --recursive"
            }
        }
        stage('Build and Test Java Code') {
            steps {
                dir('uima-html-to-text'){
                    sh "mvn compile jib:build -Denv.BRANCH_NAME=${env.BRANCH_NAME} -Dimage=docker.crosslang.com/uima-html-to-text:${env.BRANCH_NAME}-latest"
                }
            }
        }
        stage('Deploy Helm Chart') {
            steps {
                dir('deploy/helm'){
                    sh './kompose.sh'
                }
            }
        }
    }

    post {
        success {
            slackSend (color: '#36A64F', message: "SUCCESSFUL: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})")
        }
        failure {
            slackSend (color: '#FF0000', message: "FAILED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})")
        }
    }

}


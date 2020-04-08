#!groovy

pipeline {
    environment {
        VERSION = ''
    }

    agent { label 'master' }

    stages {
        stage('Build Docker images') {
            docker.withRegistry("https://docker.crosslang.com", "docker-crosslang-com") {
                steps {
                    dir('django'){
                        script {
                            def customImage = docker.build("ctlg-manager/django:${env.BUILD_ID}", "-f Dockerfile.prod .")
                            customImage.push()
                        }
                    }
                    dir('angular'){
                        script {
                            def customImage = docker.build("ctlg-manager/angular:${env.BUILD_ID}", "-f Dockerfile .")
                            customImage.push()
                        }
                    }
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


#!groovy

pipeline {
    environment {
        VERSION = ''
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
            }
        }
    }
}


// Optional: the same pipeline as a Jenkins declarative pipeline, for comparison.
// (Not run here. Needs a Jenkins agent with Python 3 installed.)
pipeline {
  agent any
  stages {
    stage('Install') { steps { sh 'python3 -m venv .venv && . .venv/bin/activate && pip install pytest pytest-bdd' } }
    stage('Test') {
      steps { sh '. .venv/bin/activate && pytest lab1_sql_migration_checks lab4_bdd_gherkin ex7_mock_controller --junitxml=reports/all.xml' }
    }
  }
  post { always { junit 'reports/*.xml' } }
}

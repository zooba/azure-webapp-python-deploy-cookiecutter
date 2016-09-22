{% set python_package_name = 'python' + (cookiecutter.python_version|replace('.', '')) + cookiecutter.cpu_arch %}

Paste the following snippet into your JSON deployment template to create a web
app. You will need an existing parameter for the server farm named
`hostingPlanName`. The `appsettings` section is provided for convenience, but
may be removed if your app does not require any environment variables.

Once you have deployed the web app, download the publishing profile through
Cloud Explorer or from the Azure Portal and run `deploy.bat`.

```json
    {
      "apiVersion": "2015-08-01",
      "name": "{{ cookiecutter.site_name }}",
      "type": "Microsoft.Web/sites",
      "location": "[resourceGroup().location]",
      "dependsOn": [ "[resourceId('Microsoft.Web/serverfarms', parameters('hostingPlanName'))]" ],
      "properties": {
        "serverFarmId": "[parameters('hostingPlanName')]"
      },
      "resources": [
        {
          "apiVersion": "2015-08-01",
          "name": "{{ python_package_name }}",
          "type": "siteextensions",
          "properties": { },
          "dependsOn": [
            "[resourceId('Microsoft.Web/sites', '{{ cookiecutter.site_name }}')]"
          ]
        },
        {
          "apiVersion": "2015-08-01",
          "name": "logs",
          "type": "config",
          "properties": {
            "failedRequestsTracing": { "enabled": true }
          },
          "dependsOn": [
            "[resourceId('Microsoft.Web/sites', '{{ cookiecutter.site_name }}')]",
            "[resourceId('Microsoft.Web/Sites/siteextensions', '{{ cookiecutter.site_name }}', '{{ python_package_name }}')]"
          ]
        },
        {
          "apiVersion": "2015-08-01",
          "name": "appsettings",
          "type": "config",
          "dependsOn": [
            "[resourceId('Microsoft.Web/Sites', '{{ cookiecutter.site_name }}')]",
            "[resourceId('Microsoft.Web/Sites/siteextensions', '{{ cookiecutter.site_name }}', '{{ python_package_name }}')]",
            "[resourceId('Microsoft.Web/Sites/config', '{{ cookiecutter.site_name }}', 'logs')]"
          ],
          "properties": {
              "EXAMPLE_SETTING": "example value"
          }
        }
      ]
    }
```
# Sandbox-API-Python
Sandbox API Python wrapper

**Usage:**
```
blueprint_name = "Sandbox Python API Test"
sandbox_name = "Sandbox Python API Test"
config_file = "quali_config.json"

my_sandbox = Sandbox(config_file=config_file)
my_sandbox.login()

my_sandbox.get_blueprints()
blueprint_id = my_sandbox.get_blueprint_id(blueprint_name=blueprint_name)
print "Blueprint Id:", blueprint_id
my_sandbox.get_blueprint_details(blueprint_id=blueprint_id)
my_sandbox.get_blueprint_details_by_name(blueprint_name=blueprint_name)

my_sandbox.start_sandbox(blueprint_id=blueprint_id, duration='20', sandbox_name='')
my_sandbox.start_sandbox_by_name(blueprint_name=blueprint_name, duration='20', sandbox_name='')
my_sandbox.get_sandboxes()
sandbox_id = my_sandbox.get_sandbox_ids(sandbox_name=sandbox_name)
print "Sandbox Id:", sandbox_id
my_sandbox.get_sandbox_details(sandbox_id=sandbox_id[0])
my_sandbox.get_sandboxes_details_by_name(sandbox_name=sandbox_name)
my_sandbox.stop_sandbox(sandbox_id=sandbox_id[0])
my_sandbox.stop_sandboxes_by_name(sandbox_name=sandbox_name)
```

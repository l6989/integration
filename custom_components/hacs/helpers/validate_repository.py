"""Helper to do common validation for repositories."""
from custom_components.hacs.hacsbase.exceptions import HacsException
from custom_components.hacs.helpers.install import version_to_install
from custom_components.hacs.helpers.information import get_repository, get_tree


async def common_validate(hacs, repository):
    """Common validation steps of the repository."""
    repository.validate.errors = []

    # Step 1: Make sure the repository exist.
    repository.logger.debug("Checking repository.")
    try:
        repository.repository_object = await get_repository(
            hacs.session, hacs.configuration.token, repository.information.full_name
        )
        repository.data = repository.data.create_from_dict(
            repository.repository_object.attributes
        )
    except HacsException as exception:
        if not hacs.system.status.startup:
            repository.logger.error(exception)
        repository.validate.errors.append("Repository does not exist.")
        raise HacsException(exception)

    if repository.ref is None:
        repository.ref = version_to_install(repository)

    try:
        repository.tree = await get_tree(repository.repository_object, repository.ref)
        repository.treefiles = []
        for treefile in repository.tree:
            repository.treefiles.append(treefile.full_path)
    except HacsException as exception:
        if not hacs.system.status.startup:
            repository.logger.error(exception)
        raise HacsException(exception)

    # Step 2: Make sure the repository is not archived.
    if repository.data.archived:
        repository.validate.errors.append("Repository is archived.")
        raise HacsException("Repository is archived.")

    # Step 3: Make sure the repository is not in the blacklist.
    if repository.data.full_name in hacs.common.blacklist:
        repository.validate.errors.append("Repository is in the blacklist.")
        raise HacsException("Repository is in the blacklist.")

    # Step 5: Get releases.
    await repository.get_releases()

    # Step 6: Get the content of hacs.json
    await repository.get_repository_manifest_content()

    # Set repository name
    repository.information.name = repository.information.full_name.split("/")[1]

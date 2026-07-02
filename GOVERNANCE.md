# Kubestellar Project Governance

[Instructions](https://contribute.cncf.io/maintainers/github/templates/required/governance-subprojects/)

- [Values](#values)
- [Individual Subroject Governance](#individual-subproject-governance)
- [Steering Committee](#steering-committee)
  - [Steering Committee Duties](#steering-committee-duties)
  - [Steering Committee Elections](#steering-committee-elections)
- [Code of Conduct Committee](#code-of-conduct-committee)
- [Adding New Subprojects](#adding-new-subprojects)
- [Removing Projects](#removing-projects)

## Values

[Instructions](https://contribute.cncf.io/maintainers/github/templates/required/governance-subprojects/#values)

The [TODO: PROJECTNAME] and its leadership embrace the following values:

* Openness: Communication and decision-making happens in the open and is discoverable for future
  reference. As much as possible, all discussions and work take place in public
  forums and open repositories.

* Fairness: All stakeholders have the opportunity to provide feedback and submit
  contributions, which will be considered on their merits.

* Community over Product or Company: Sustaining and growing our community takes
  priority over shipping code or sponsors' organizational goals.  Each
  contributor participates in the project as an individual.

* Inclusivity: We innovate through different perspectives and skill sets, which
  can only be accomplished in a welcoming and respectful environment.

* Participation: Responsibilities within the project are earned through
  participation, and there is a clear path up the contributor ladder into leadership
  positions.

## Kubestellar Subproject Governance

Kubestellar hosts subprojects within its umbrella. The governance principles are the same across all of Kubestellar: 

- [Hive](example)

All active Maintainers of each subproject, as defined in the Contributor Ladder, are
members of that subproject's Maintainer Committee, which governs that project.  The
subproject's Maintainer Committee is responsible for the following project governance
activities:

* Ensuring that the subproject creates and publishes regular releases;
* Holding regular, subproject-wide discussions on issues and planning;
* Monthly review of project contributors for advancement on the Contributor Ladder;
* Making final decisions on subproject changes that involve controversial trade-offs;
* Responding to security compromise reports;
* Supporting the Code of Conduct within their subproject and referring violations
  to the Code of Conduct Committee.

### Adding New Subprojects

To become a Kubestellar subproject:

* Have a mission alignment with Kubestellar
* Are appropriately licensed and governed or willing to become so;
* Are under active development;
* Consist of high quality code and designs.

The applying project MUST hold an internal consensus vote of all major contributors to join Kubestellar.
In some cases, promising but incomplete projects may be accepted as Experimental
Subprojects. These will be marked as Experimental and documented as such to set user expectations. 
Maintainers will review Experimental projects twice a year to determine if they have matured to full subproject status.

All subproject members are considered Kubestellar maintainers. 

## Removing Projects

In some cases, projects will become inactive or unmaintainable, or wish to separate
from Kubestellar. Any contributor may propose removal of a 
project on these grounds.

Subprojects which still have contributors will then be moved to a repository in 
their own namespace. Projects which have ceased all activity are moved to a
[TODO:Name of archive namespace] namespace.

## Amendments

This governance document, and other governance documents of Kubestellar
can be amended with a 2/3 majority vote of the maintainers as defined by OWNERS (and whatever else).
Unless time is of the essence, the amendment should be circulated in the contributor community for 
comment for at least one week before voting.

# Release Notes - {{next_release_tag}}

Please see our [documentation](https://repo1.dso.mil/platform-one/big-bang/bigbang/-/tree/{{next_release_tag}}) page for more information on how to consume and deploy BigBang.

## Upgrade Notices

> For each upgraded package, you will have to either reach out to the
> package maintainers, or read through the changelog/commit diffs to figure
> out any pertinent upgrade notices.
>
> I have included a potential list of packages to look at below.
>
> Please review, then add any explanations as needed to that packages section
> under `## Changes in {{next_release_tag}}`
>
> Good luck.
>

| Package | Commit Diffs | From | To   |
| :------ | :----------- | :--- | :--- |
{% for pkg in upgraded_packages %}
| {{pkg["title"]}} [↓](#{{pkg["name"]}}) | [Commit Diffs]({{pkg["url"]}}/-/compare/{{pkg["last_tag"]}}...{{pkg["tag"]}}) | `{{pkg["last_tag"]}}` | `{{pkg["tag"]}}` |
{% endfor %}

### **Upgrades from previous releases**

If coming from a version pre-`{{last_release}}`, note the additional upgrade notices in any release in between. The BB team doesn't test/guarantee upgrades from anything pre-`{{last_release}}`.

## Packages

{{packages_table}}

## Changes in {{next_release_tag}}

### Big Bang MRs

> Parsing this MR list programatically has no guarantee to be accurate
> due to the nonstandard format of labeling our MRs.
> 
> Because of this, you will have to break out this list manually,
> and move each MR under the package it belongs to / deals with.

{% for mr in mr_changes %}
- [{{mr.reference}}]({{mr.web_url}}): {{mr.title}}
{% endfor %}

{% for title,changes in changelog_diffs.items() %}

### {{title}}

```markdown
# Changelog Updates

{{changes}}
```

{% endfor %}

## Known Issues

- On some k8s distros certain components in the kube-system namespace are unable to be scraped by Prometheus
- Prometheus scrapes completed pods, this doesn't affect anything but may see some "Down" targets in Prometheus UI - [Monitoring !43](https://repo1.dso.mil/platform-one/big-bang/apps/core/monitoring/-/issues/43) 
- Grafana may fail to start on airgap clusters in certain scenarios due to the pod attempting to download plugins - [!1053](https://repo1.dso.mil/platform-one/big-bang/bigbang/-/issues/1053)

    As a temporary workaround you can set the below values so that the pods do not attempt to download the plugins (may result in some missing panels on Gitlab Runner and/or Loki dashboards):

    ```yaml
    monitoring:
      values:
        grafana:
          plugins: []
    ```

## Helpful Links

As always, we welcome and appreciate feedback from our community of users. Please feel free to:

- [Open issues here](https://repo1.dso.mil/platform-one/big-bang/umbrella/-/issues/new?issue%5Bassignee_id%5D=&issue%5Bmilestone_id%5D=)
- [Join our chat](https://chat.il2.dso.mil/platform-one/channels/team---big-bang)
- Check out the [documentation](https://repo1.dso.mil/platform-one/big-bang/bigbang/-/tree/master/docs) for guidance on how to get started

## Future

Don't see your feature and/or bug fix? Check out our [epics](https://repo1.dso.mil/groups/platform-one/big-bang/-/epic_boards/7) for estimates on when you can expect things to drop, and as always, feel free to comment or create issues if you have questions, comments, or concerns.

const selected = new URLSearchParams(window.location.search).get("lab");
const name = selected === "baseline" ? "baseline" : "diamond";
document.getElementById(name).setAttribute("aria-current", "page");

async function read(relativePath) {
    const response = await fetch(relativePath);
    if (!response.ok) throw new Error(relativePath + ": HTTP " + response.status);
    return response.text();
}

try {
    const [yaml, annotations] = await Promise.all([
        read("./" + name + ".clab.yml"),
        read("./" + name + ".clab.yml.annotations.json"),
    ]);
    await customElements.whenDefined("clab-topology");

    const topology = document.createElement("clab-topology");
    const source = document.createElement("pre");
    source.textContent = yaml;
    topology.append(source);

    const attributes = {
        title: name === "baseline" ? "PCEP and telemetry" : "Services and protection",
        filename: name + ".clab.yml",
        annotations,
        theme: "light",
        view: "topology",
        inspector: "",
        controls: "",
        grid: "dots",
        "link-labels": "on-select",
        "link-hover": "",
        zoom: "false",
        loading: "eager",
    };
    for (const [key, value] of Object.entries(attributes)) topology.setAttribute(key, value);
    document.getElementById("diagram").replaceChildren(topology);
} catch (error) {
    console.error("Could not load the Containerlab viewer", error);
}

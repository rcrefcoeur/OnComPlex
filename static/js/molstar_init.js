document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("molstar-viewer");
    if (!container) return;

    const uniprot = container.dataset.uniprot;
    if (!uniprot) return;

    const viewer = new Molstar.Viewer(container, {
        layout: "auto",
        theme: "light"
    });

    // Load AlphaFold structure by UniProt ID
    viewer.loadStructureFromUrl(
        `https://alphafold.ebi.ac.uk/files/AF-${uniprot}-F1-model_v4.pdb`,
        "pdb"
    );
});

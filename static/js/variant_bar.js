document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".variant-bar").forEach(bar => {
        const length = parseInt(bar.dataset.length);
        const variants = JSON.parse(bar.dataset.variants);

        const width = 700;
        const height = 20;

        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("width", width);
        svg.setAttribute("height", height);

        // backbone
        const backbone = document.createElementNS(svg.namespaceURI, "rect");
        backbone.setAttribute("x", 0);
        backbone.setAttribute("y", height / 2 - 2);
        backbone.setAttribute("width", width);
        backbone.setAttribute("height", 4);
        backbone.setAttribute("fill", "#bbb");
        svg.appendChild(backbone);

        variants.forEach(v => {
            const x = Math.max(0, Math.min(width, (v.pos / length) * width));

            const dot = document.createElementNS(svg.namespaceURI, "circle");
            dot.setAttribute("cx", x);
            dot.setAttribute("cy", height / 2);
            dot.setAttribute("r", 5);
            dot.setAttribute("fill", colorForType(v.type));

            dot.title = `${v.mutation} (${v.type}) @ ${v.pos}`;
            svg.appendChild(dot);
        });

        bar.appendChild(svg);
    });
});

function colorForType(type) {
    if (!type) return "#888";
    if (type.includes("Missense")) return "#1f77b4";
    if (type.includes("Nonsense")) return "#d62728";
    if (type.includes("Frameshift")) return "#9467bd";
    if (type.includes("In frame")) return "#2ca02c";
    return "#ff7f0e";
}

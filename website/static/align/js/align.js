"use strict"

/**
 * Align multiple genes.
 */
async function load_alignment(gene_identifiers, target_div, method = 'clustalo', sequence_type = 'protein') {
    console.log('start MSA:', gene_identifiers, target_div, method, sequence_type);

    let result
    await $.post('/api/align/', {'gene_identifiers': gene_identifiers, 'method': method, 'sequence_type': sequence_type}, function (data) {
        console.log('MSA complete:', data)

        const seqs = msa.io.fasta.parse(data['alignment'])

        let opts = {
            seqs: seqs,
            el: target_div[0],
            vis: {
                conserv: false,
                overviewbox: false
            },
            // smaller menu for JSBin
            menu: "small",
            bootstrapMenu: true
        }

        let m = msa(opts)

        m.g.zoomer.set("alignmentHeight", seqs.length * 15)
        m.g.zoomer.set("labelNameLength", Math.max(...seqs.map((s) => s.name.length)) * 7.1 + 15)

        m.render()

        result = data['alignment']

    }, "json").fail(function (data) {
        const msg = data.responseJSON['message']
        console.log(msg)
        target_div.append(`
        <div class="alert alert-warning" role="alert">
                ${msg}
        </div>
        `)

        result = 'failure'
    })

    return result
}
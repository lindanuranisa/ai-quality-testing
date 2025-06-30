Cypress.Commands.add('loginByGoogleApi', () => {
    const accessToken = Cypress.env('accessToken'); // Get access token from env file
  
    window.localStorage.setItem('oracle-persist', JSON.stringify({ apiToken: Cypress.env('apiKey') }));
    cy.reload();
  
    cy.request({
      method: 'POST',
      failOnStatusCode: false,
      url: 'https://alphame-api.adgo.dev/api/v1/account/login/',
      body: {
        access_token: accessToken, // Use the retrieved token
        type: "google"
      },
    }).then((r) => console.log(r));
  
    console.log(accessToken);
  
    window.localStorage.setItem('oracle-persist', JSON.stringify({ apiToken: Cypress.env('apiKey') }));
    cy.reload();
  });


  Cypress.Commands.add('extractCompanyFields', (verifyRecords) => {
    const fields = [
        { label: 'Company name', key: 'company_name' },
        { label: 'Industry', key: 'industry' },
        { label: 'Location', key: 'location' },
        { label: 'Founders', key: 'founders' },
        { label: 'Founder Email', key: 'founder_email' },
        { label: 'Year Founded', key: 'year_founded' },
        { label: 'Funding Stage', key: 'funding_stage' },
        { label: 'Latest Valuation', key: 'latest_valuation' },
        { label: 'Fund Raise Target', key: 'fund_raise_target' },
        { label: 'Amount Raised', key: 'amount_raised' },
        { label: 'Revenue', key: 'revenue' },
        { label: 'List of investors', key: 'list_of_investors' },
        { label: 'Lead Investor', key: 'lead_investor' },
        { label: 'Verticals', key: 'verticals' },
        { label: 'Keywords', key: 'keywords' }
    ];

    // Extract each field using your working logic
    fields.forEach(({ label, key }) => {
        cy.get('body').then($body => {
            const $label = $body.find(`[class*="text-content-secondary"]:contains("${label}")`);
            if ($label.length > 0) {
                const $container = $label.closest('div[class*="rounded"]');
                const $valueEl = $container.find([
                    'div.mt-1.line-clamp-2.text-sm.font-medium.text-content-primary',
                    'span.text-sm.font-medium.text-content-primary',
                    '[class*="font-medium"][class*="text-content-primary"]'
                ].join(', ')).first();
                
                if ($valueEl.length > 0) {
                    const value = $valueEl.text().trim();
                    verifyRecords[key] = value;
                    cy.log(`📝 ${label}: ${value || 'Not found'}`);
                } else {
                    cy.log(`⚠️  ${label}: Value element not found`);
                }
            } else {
                cy.log(`⚠️  ${label}: Label not found`);
            }
        });
    });
});
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Load & Clean
df = pd.read_csv('online_retail_II.csv')
df = df.dropna(subset=['Customer ID'])
df = df[~df['Invoice'].astype(str).str.startswith('C')]
df = df[df['Quantity'] > 0]
df = df[df['Price'] > 0]
df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
df['TotalSales'] = df['Quantity'] * df['Price']

# RFM
ref_date = df['InvoiceDate'].max()
rfm = df.groupby('Customer ID').agg(
    Recency=('InvoiceDate', lambda x: (ref_date - x.max()).days),
    Frequency=('Invoice', 'nunique'),
    Monetary=('TotalSales', 'sum')
).reset_index()

rfm['R_Score'] = pd.qcut(rfm['Recency'], q=4, labels=[4,3,2,1])
rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), q=4, labels=[1,2,3,4])
rfm['M_Score'] = pd.qcut(rfm['Monetary'], q=4, labels=[1,2,3,4])

def segment(row):
    r = int(row['R_Score'])
    f = int(row['F_Score'])
    m = int(row['M_Score'])
    if r >= 3 and f >= 3 and m >= 3:
        return 'VIP'
    elif r >= 3 and f >= 2:
        return 'Loyal'
    elif r <= 2 and f >= 3:
        return 'At Risk'
    elif r == 1 and f == 1:
        return 'Lost'
    else:
        return 'Potential'

rfm['Segment'] = rfm.apply(segment, axis=1)

# Segment Summary
summary = rfm.groupby('Segment').agg(
    Customers=('Customer ID', 'count'),
    Avg_Spend=('Monetary', 'mean'),
    Avg_Frequency=('Frequency', 'mean'),
    Avg_Recency=('Recency', 'mean')
).round(2)

print("=== SEGMENT SUMMARY ===")
print(summary)

# Campaign Recommendations
campaigns = {
    'VIP':       ('gold',      'Exclusive Loyalty Program',  'Early access, VIP discounts, Free shipping'),
    'Potential': ('green',     'Upsell Campaign',            'Product bundles, "You might also like" emails'),
    'Loyal':     ('steelblue', 'Reward Program',             'Points system, Birthday discounts'),
    'At Risk':   ('orange',    'Win-back Campaign',          '"We miss you" email, 20% off coupon'),
    'Lost':      ('red',       'Re-engagement Campaign',     'Big discount offer, Survey to understand why'),
}

# Campaign Chart
fig, ax = plt.subplots(figsize=(14, 8))
ax.axis('off')

headers = ['Segment', 'Customers', 'Avg Spend (£)', 'Campaign', 'Strategy']
x_positions = [0.02, 0.14, 0.24, 0.37, 0.59]

# Header
for h, x in zip(headers, x_positions):
    ax.text(x, 0.92, h, fontsize=11, fontweight='bold', transform=ax.transAxes)

ax.axhline(y=0.90, xmin=0.02, xmax=0.98, color='black', linewidth=1)

# Rows
y = 0.80
for seg, (color, campaign, strategy) in campaigns.items():
    if seg in summary.index:
        customers = int(summary.loc[seg, 'Customers'])
        avg_spend = summary.loc[seg, 'Avg_Spend']
        ax.add_patch(mpatches.FancyBboxPatch(
            (x_positions[0]-0.01, y-0.04), 0.10, 0.08,
            boxstyle="round,pad=0.01", color=color, alpha=0.3,
            transform=ax.transAxes))
        ax.text(x_positions[0], y, seg, fontsize=10, fontweight='bold', color=color, transform=ax.transAxes)
        ax.text(x_positions[1], y, str(customers), fontsize=10, transform=ax.transAxes)
        ax.text(x_positions[2], y, f'£{avg_spend:,.0f}', fontsize=10, transform=ax.transAxes)
        ax.text(x_positions[3], y, campaign, fontsize=10, transform=ax.transAxes)
        ax.text(x_positions[4], y, strategy, fontsize=9, transform=ax.transAxes)
        ax.axhline(y=y-0.06, xmin=0.02, xmax=0.98, color='gray', linewidth=0.5, alpha=0.5)
        y -= 0.13

ax.set_title('Data-Driven Marketing Campaign Recommendations\nBased on RFM Customer Segmentation',
             fontsize=14, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('campaign_recommendations.png', dpi=150, bbox_inches='tight')
plt.show()
print("Campaign chart saved!")
# Export for Power BI
rfm.to_csv('rfm_segments.csv', index=False)

monthly_sales = df.groupby(df['InvoiceDate'].dt.to_period('M'))['TotalSales'].sum().reset_index()
monthly_sales['InvoiceDate'] = monthly_sales['InvoiceDate'].astype(str)
monthly_sales.to_csv('monthly_sales.csv', index=False)

country_sales = df.groupby('Country')['TotalSales'].sum().reset_index()
country_sales.to_csv('country_sales.csv', index=False)

print("CSV files exported!")
-- ============================================================
-- FMCG ANALYTICS DATABASE
-- PostgreSQL VERSION
-- ============================================================


-- ============================================================
-- CUSTOMERS
-- ============================================================

CREATE TABLE IF NOT EXISTS customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    city VARCHAR(100),
    registration_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE INDEX IF NOT EXISTS idx_customers_name
ON customers(name);


CREATE INDEX IF NOT EXISTS idx_customers_city
ON customers(city);



-- ============================================================
-- SUPPLIERS
-- ============================================================

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    phone VARCHAR(50),
    email VARCHAR(255),
    rating NUMERIC(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE INDEX IF NOT EXISTS idx_suppliers_name
ON suppliers(name);



-- ============================================================
-- PRODUCTS
-- ============================================================

CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    brand VARCHAR(100),
    supplier_id INTEGER,
    unit VARCHAR(50) DEFAULT 'pcs',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(supplier_id)
    REFERENCES suppliers(supplier_id)
    ON DELETE SET NULL
);


CREATE INDEX IF NOT EXISTS idx_products_category
ON products(category);


CREATE INDEX IF NOT EXISTS idx_products_brand
ON products(brand);


CREATE INDEX IF NOT EXISTS idx_products_supplier
ON products(supplier_id);



-- ============================================================
-- PRODUCT PRICES
-- ============================================================

CREATE TABLE IF NOT EXISTS product_prices (

    price_id SERIAL PRIMARY KEY,

    product_id INTEGER NOT NULL,

    year INTEGER NOT NULL,

    cost_price NUMERIC(12,2) NOT NULL,

    selling_price NUMERIC(12,2),


    FOREIGN KEY(product_id)
    REFERENCES products(product_id)
    ON DELETE CASCADE,


    UNIQUE(product_id, year)
);


CREATE INDEX IF NOT EXISTS idx_product_prices_product
ON product_prices(product_id);


CREATE INDEX IF NOT EXISTS idx_product_prices_year
ON product_prices(year);



-- ============================================================
-- ORDERS
-- ============================================================

CREATE TABLE IF NOT EXISTS orders (

    order_id SERIAL PRIMARY KEY,

    customer_id INTEGER,

    order_date DATE NOT NULL,

    status VARCHAR(50)
    DEFAULT 'completed',

    shipping_address TEXT,

    total_amount NUMERIC(12,2),


    FOREIGN KEY(customer_id)
    REFERENCES customers(customer_id)
    ON DELETE SET NULL
);



CREATE INDEX IF NOT EXISTS idx_orders_customer
ON orders(customer_id);


CREATE INDEX IF NOT EXISTS idx_orders_date
ON orders(order_date);



-- ============================================================
-- ORDER ITEMS
-- ============================================================

CREATE TABLE IF NOT EXISTS order_items (

    order_item_id SERIAL PRIMARY KEY,

    order_id INTEGER NOT NULL,

    product_id INTEGER NOT NULL,

    quantity INTEGER NOT NULL
    CHECK(quantity > 0),

    price NUMERIC(12,2)
    CHECK(price >= 0),


    FOREIGN KEY(order_id)
    REFERENCES orders(order_id)
    ON DELETE CASCADE,


    FOREIGN KEY(product_id)
    REFERENCES products(product_id)
    ON DELETE RESTRICT
);



CREATE INDEX IF NOT EXISTS idx_order_items_order
ON order_items(order_id);


CREATE INDEX IF NOT EXISTS idx_order_items_product
ON order_items(product_id);



-- ============================================================
-- INVENTORY
-- ============================================================

CREATE TABLE IF NOT EXISTS inventory (

    inventory_id SERIAL PRIMARY KEY,

    product_id INTEGER NOT NULL,

    stock_quantity INTEGER DEFAULT 0,

    reorder_point INTEGER DEFAULT 0,

    max_stock INTEGER,

    warehouse VARCHAR(100),

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,


    FOREIGN KEY(product_id)
    REFERENCES products(product_id)
    ON DELETE CASCADE,


    UNIQUE(product_id, warehouse)
);



CREATE INDEX IF NOT EXISTS idx_inventory_product
ON inventory(product_id);


CREATE INDEX IF NOT EXISTS idx_inventory_stock
ON inventory(stock_quantity);



-- ============================================================
-- INVENTORY MOVEMENTS
-- ============================================================

CREATE TABLE IF NOT EXISTS inventory_movements (

    movement_id SERIAL PRIMARY KEY,

    product_id INTEGER NOT NULL,

    movement_date DATE NOT NULL,

    movement_type VARCHAR(50),

    quantity INTEGER NOT NULL,

    unit_cost NUMERIC(12,2),


    FOREIGN KEY(product_id)
    REFERENCES products(product_id)
    ON DELETE CASCADE
);



CREATE INDEX IF NOT EXISTS idx_inventory_movements_product
ON inventory_movements(product_id);



-- ============================================================
-- CARRIERS
-- ============================================================

CREATE TABLE IF NOT EXISTS carriers (

    carrier_id SERIAL PRIMARY KEY,

    name VARCHAR(255) NOT NULL,

    region VARCHAR(100),

    phone VARCHAR(50),

    rating NUMERIC(3,2),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



CREATE INDEX IF NOT EXISTS idx_carriers_name
ON carriers(name);



-- ============================================================
-- ROUTES
-- ============================================================

CREATE TABLE IF NOT EXISTS routes (

    route_id SERIAL PRIMARY KEY,

    route_name VARCHAR(255),

    origin VARCHAR(255),

    destination VARCHAR(255),

    region VARCHAR(100),

    distance_km NUMERIC(10,2)

);



CREATE INDEX IF NOT EXISTS idx_routes_region
ON routes(region);



-- ============================================================
-- LOGISTICS
-- ============================================================

CREATE TABLE IF NOT EXISTS logistics (

    logistics_id SERIAL PRIMARY KEY,

    order_id INTEGER,

    carrier_id INTEGER,

    route_id INTEGER,

    shipment_date DATE,

    delivery_date DATE,

    distance_km NUMERIC(10,2),

    delivery_time_hours NUMERIC(10,2),

    logistics_cost NUMERIC(12,2),

    delay_minutes INTEGER DEFAULT 0,

    sla_status VARCHAR(50),


    FOREIGN KEY(order_id)
    REFERENCES orders(order_id)
    ON DELETE SET NULL,


    FOREIGN KEY(carrier_id)
    REFERENCES carriers(carrier_id)
    ON DELETE SET NULL,


    FOREIGN KEY(route_id)
    REFERENCES routes(route_id)
    ON DELETE SET NULL
);



CREATE INDEX IF NOT EXISTS idx_logistics_order
ON logistics(order_id);


CREATE INDEX IF NOT EXISTS idx_logistics_carrier
ON logistics(carrier_id);


CREATE INDEX IF NOT EXISTS idx_logistics_date
ON logistics(shipment_date);



-- ============================================================
-- VIEWS
-- ============================================================


CREATE OR REPLACE VIEW sales_details AS

SELECT

    o.order_id,

    o.order_date,

    c.name AS customer_name,

    p.product_id,

    p.name AS product_name,

    p.category,

    p.brand,

    oi.quantity,

    oi.price,

    oi.quantity * oi.price AS revenue


FROM orders o


JOIN order_items oi

ON oi.order_id = o.order_id


JOIN products p

ON p.product_id = oi.product_id


LEFT JOIN customers c

ON c.customer_id = o.customer_id;



-- ============================================================
-- PROFIT VIEW
-- ============================================================


CREATE OR REPLACE VIEW product_profit_details AS

SELECT

    o.order_id,

    o.order_date,

    p.product_id,

    p.name AS product_name,

    oi.quantity,

    oi.price AS selling_price,

    pp.cost_price,


    oi.quantity *
    (
        oi.price -
        pp.cost_price
    ) AS profit,


    oi.quantity *
    oi.price AS revenue


FROM order_items oi


JOIN orders o

ON o.order_id = oi.order_id


JOIN products p

ON p.product_id = oi.product_id


LEFT JOIN product_prices pp

ON pp.product_id = oi.product_id


AND pp.year =
EXTRACT(
    YEAR FROM o.order_date
);



-- ============================================================
-- INVENTORY VALUE VIEW
-- ============================================================


CREATE OR REPLACE VIEW inventory_value_details AS

SELECT

    i.inventory_id,

    p.name AS product_name,

    p.category,

    p.brand,


    i.stock_quantity,


    pp.cost_price,


    i.stock_quantity *
    pp.cost_price AS inventory_value


FROM inventory i


JOIN products p

ON p.product_id = i.product_id


LEFT JOIN product_prices pp

ON pp.product_id = i.product_id


AND pp.year =
(
    SELECT MAX(pp2.year)

    FROM product_prices pp2

    WHERE pp2.product_id =
    i.product_id
);



-- ============================================================
-- LOGISTICS VIEW
-- ============================================================


CREATE OR REPLACE VIEW logistics_details AS

SELECT

    l.logistics_id,

    l.order_id,

    l.shipment_date,

    l.delivery_date,

    l.distance_km,

    l.delivery_time_hours,

    l.logistics_cost,

    l.delay_minutes,

    l.sla_status,


    c.name AS carrier_name,


    r.route_name,

    r.origin,

    r.destination


FROM logistics l


LEFT JOIN carriers c

ON c.carrier_id = l.carrier_id


LEFT JOIN routes r

ON r.route_id = l.route_id;
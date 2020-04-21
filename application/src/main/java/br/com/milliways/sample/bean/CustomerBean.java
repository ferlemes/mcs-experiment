/*
 * Copyright 2020, Fernando Lemes da Silva
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package br.com.milliways.sample.bean;

/**
 * This class represents a Customer bean.
 */
public class CustomerBean {

    /**
     * The id of the customer.
     */
    private Integer id;

    /**
     * The name of the customer.
     */
    private String name;

    /**
     * Get the id of the customer.
     *
     * @return the id of the customer.
     */
    public Integer getId() {
        return id;
    }

    /**
     * Set the id of the customer.
     *
     * @param id of the customer.
     */
    public void setId(Integer id) {
        this.id = id;
    }

    /**
     * Get the name of the customer.
     *
     * @return the name of the customer.
     */
    public String getName() {
        return name;
    }

    /**
     * Set the name of the customer.
     *
     * @param name of the customer.
     */
    public void setName(String name) {
        this.name = name;
    }

}

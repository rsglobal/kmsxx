#include <string.h>
#include <iostream>
#include <stdexcept>

#include <xf86drm.h>
#include <xf86drmMode.h>

#include "kms++.h"

using namespace std;

namespace kms
{

DrmObject::DrmObject(Card& card, uint32_t object_type)
	:m_card(card), m_id(-1), m_object_type(object_type), m_idx(0)
{
}

DrmObject::DrmObject(Card& card, uint32_t id, uint32_t object_type, uint32_t idx)
	:m_card(card), m_id(id), m_object_type(object_type), m_idx(idx)
{
	refresh_props();
}

DrmObject::~DrmObject()
{

}

void DrmObject::refresh_props()
{
	auto props = drmModeObjectGetProperties(card().fd(), this->id(), this->object_type());

	if (props == nullptr)
		return;

	for (unsigned i = 0; i < props->count_props; ++i) {
		uint32_t prop_id = props->props[i];
		uint64_t prop_value = props->prop_values[i];

		m_prop_values[prop_id] = prop_value;
	}

	drmModeFreeObjectProperties(props);
}

uint64_t DrmObject::get_prop_value(uint32_t id) const
{
	return m_prop_values.at(id);
}

uint64_t DrmObject::get_prop_value(const string& name) const
{
	for (auto pair : m_prop_values) {
		auto prop = card().get_prop(pair.first);
		if (name == prop->name())
			return m_prop_values.at(prop->id());
	}

	throw invalid_argument("property not found: " + name);
}

int DrmObject::set_prop_value(uint32_t id, uint64_t value)
{
	return drmModeObjectSetProperty(card().fd(), this->id(), this->object_type(), id, value);
}

int DrmObject::set_prop_value(const string &name, uint64_t value)
{
	Property* prop = card().get_prop(name);

	if (prop == nullptr)
		throw invalid_argument("property not found: " + name);

	return set_prop_value(prop->id(), value);
}

void DrmObject::set_id(uint32_t id)
{
	m_id = id;
}
}
